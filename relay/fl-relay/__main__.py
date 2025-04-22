import argparse
import json
import socket
import time

import flomqtt.serialize as flserialize

import requests

def main(args):

    # Set up listener.
    lpo_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    lpo_addrinfo = socket.getaddrinfo(args.address, args.listen_port, socket.AF_INET6, socket.SOCK_DGRAM)[0]
    lpo_socket.bind(lpo_addrinfo[4])

    # Track clients' offloads (address -> (last recv, data))
    clients = {}
    while True:
        payload, src_addr = lpo_socket.recvfrom(1024)
        if src_addr not in clients.keys():
            clients[src_addr] = (time.time(), payload)
        else:
            last_seen = clients[src_addr][0]
            current_data = clients[src_addr][1]

            if time.time() - last_seen > 3.0:
                print('dumping {} bytes from {}'.format(
                    len(current_data),
                    src_addr))
                del clients[src_addr]
                clients[src_addr] = (time.time(), payload)
            else:
                new_data = current_data + payload
                if len(new_data) >= 8192:
                    print('relaying to FL')
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
                        print('server says:')
                        for line in response.iter_lines():
                            print(line)
                    except requests.exceptions.ConnectionError:
                        print('...cannot connect to server.')
                    del clients[src_addr]
                else:
                    # Just effectively append the new data.
                    clients[src_addr] = (time.time(), new_data)
                    print('collected {} bytes from {}'.format(
                        len(new_data),
                        src_addr))

if __name__ == '__main__':

    ap = argparse.ArgumentParser(description='Relay FL LPO traffic.')
    ap.add_argument('-p', '--listen-port', help='LPO listener port.',
                    dest='listen_port', type=int, default=12122)

    ap.add_argument('address', help='Listen address.',
                    type=str)
    ap.add_argument('controller', help='Controller address and port.')

    args = ap.parse_args()

    main(args)
