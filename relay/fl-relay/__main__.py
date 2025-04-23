import argparse
import json
import socket
import threading
import time

import flomqtt.serialize as flserialize

import requests

def main(args):

    rr_thread = threading.Thread(name='response-receiver',
                                 target=_response_receiver,
                                 args=(args.address, args.lpo,))
    rr_thread.start()

    # Set up listener.
    lpo_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    lpo_addrinfo = socket.getaddrinfo(args.address, args.listen_port, socket.AF_INET6, socket.SOCK_DGRAM)[0]
    lpo_socket.bind(lpo_addrinfo[4])

    # Track clients' offloads (address -> (last recv, data))
    print('[offl-relay] started')
    clients = {}
    while True:
        payload, src_addr = lpo_socket.recvfrom(1024)
        if src_addr not in clients.keys():
            clients[src_addr] = (time.time(), payload)
        else:
            last_seen = clients[src_addr][0]
            current_data = clients[src_addr][1]

            if time.time() - last_seen > 3.0:
                print('[offl-relay] dumping {} bytes from {}'.format(
                    len(current_data),
                    src_addr))
                del clients[src_addr]
                clients[src_addr] = (time.time(), payload)
            else:
                new_data = current_data + payload
                if len(new_data) >= 8192:
                    print('[offl-relay] relaying to FL')
                    task_data = {
                        'device_id': 1128,
                        'task_id': 62,
                        'job_id': 0,
                        'schedule_on_executor': 0,
                        'deadline': 5000,
                    }
                    post_data = flserialize.pack(json.dumps(task_data), new_data[:8192])
                    controller_url = f'http://{args.controller}/submit-task'
                    try:
                        response = requests.post(
                            controller_url,
                            data=post_data,
                            headers={'Content-Type': 'application/octet-stream'})
                    except requests.exceptions.ConnectionError:
                        print('[offl-relay] ...cannot connect to server.')
                    del clients[src_addr]
                else:
                    # Just effectively append the new data.
                    clients[src_addr] = (time.time(), new_data)
                    print('[offl-relay] collected {} bytes from {}'.format(
                        len(new_data),
                        src_addr))

def _response_receiver(br_bind_address, offloader_addr):
    '''Entry for thread handling task responses.
    '''

    lpo_send_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.bind(('', 12123,))

    print('[cont-relay] started')
    while True:
        payload, src_addr = recv_sock.recvfrom(1024)
        print(f'received from {src_addr}: {payload}')
        lpo_send_socket.sendto(payload, (offloader_addr, 12122,))


if __name__ == '__main__':

    ap = argparse.ArgumentParser(description='Relay FL LPO traffic.')
    ap.add_argument('-p', '--listen-port', help='LPO listener port.',
                    dest='listen_port', type=int, default=12122)

    ap.add_argument('address', help='Listen address.',
                    type=str)
    ap.add_argument('controller', help='Controller address and port.')
    ap.add_argument('lpo', help='Address of the low-power offloader',
                    type=str)

    args = ap.parse_args()

    main(args)
