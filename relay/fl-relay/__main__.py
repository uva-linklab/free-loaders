import argparse
import json
import socket
import threading
import time
import sys

import flomqtt.serialize as flserialize

import gpiozero
import requests

def main(args):

    # Set up GPIO.
    gpio_thread = threading.Thread(name='gpio-watcher',
                                   target=_gpio_watcher)
    gpio_thread.start()

    # Set up controller response receiver.
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
        now = time.time()
        if src_addr not in clients.keys():
            clients[src_addr] = (now, payload)
            print(f'[offl-relay] received initial payload at {now:.3f}')
        else:
            last_seen = clients[src_addr][0]
            current_data = clients[src_addr][1]

            if time.time() - last_seen > 3.0:
                print('[offl-relay] dumping {} bytes from {}'.format(
                    len(current_data),
                    src_addr))
                del clients[src_addr]
                clients[src_addr] = (now, payload)
                print(f'[offl-relay] received initial payload at {now:.3f}')
            else:
                new_data = current_data + payload
                packet_no = int(payload[0])
                #print(f'received packet {packet_no}')
                if packet_no == 105:
                    while len(new_data) < 8192:
                        new_data += b'\xfe'

                    print('[offl-relay] relaying to FL @{:.2f}'.format(time.time()))
                    task_data = {
                        'device_id': 1128,
                        'task_id': 62,
                        'job_id': 0,
                        'schedule_on_executor': 0,
                        'deadline': 20000,
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
                    #print(f'[offl-relay] received packet no. {int(payload[0])}')
                    #print('[offl-relay] collected {} bytes from {}'.format(
                    #    len(new_data),
                    #    src_addr))

def _response_receiver(br_bind_address, offloader_addr):
    '''Entry for thread handling task responses.
    '''

    lpo_send_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.bind(('', 12123,))

    print('[cont-relay] started')
    while True:
        payload, src_addr = recv_sock.recvfrom(1024)
        print(f'received from {src_addr}: {payload} at {time.time():.2f}')
        lpo_send_socket.sendto(payload, (offloader_addr, 12122,))

_gpio_set_at = 0.0

def _gpio_edge_rising():
    global _gpio_set_at

    _gpio_set_at = time.time()
    print(f'[gw] set at {_gpio_set_at:.3f}')

def _gpio_edge_falling():
    global _gpio_set_at

    gpio_cleared_at = time.time()
    print(f'[gw] cleared at {time.time():.3f} after {gpio_cleared_at - _gpio_set_at:.3f}')

def _gpio_watcher():
    '''Entry for thread watching GPIO.
    '''

    import signal

    print('[gw] started')

    ip = gpiozero.Button(4)
    ip.when_pressed = _gpio_edge_rising
    ip.when_released = _gpio_edge_falling
    print('[gw] GPIO configured')

    while True:
        signal.pause()

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
