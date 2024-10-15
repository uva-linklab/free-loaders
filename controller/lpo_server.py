import socket
import threading
import time

LPOListenPort = 25560

def start_server(task_dispatcher):
    '''Start the low-power-offloader listener.
    '''

    lpo_listener_thread = threading.Thread(
        target=lpo_listener_main,
        name='lpo-listener',
        args=(task_dispatcher,))
    lpo_listener_thread.start()

    return lpo_listener_thread

def lpo_listener_main(task_dispatcher):
    '''Entry point for the LPO listener.
    '''

    print('[lpo] started')

    listen_ip = '0.0.0.0'
    sock = None
    while sock == None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((listen_ip, LPOListenPort,))
        except:
            print('[lpo] binding failed; retrying in 3 seconds...')
            sock = None
            time.sleep(3)
            continue

    print('[lpo] listening for LPO packets on {}:{}'.format(
        listen_ip, LPOListenPort))

    while True:
        payload, src_addr = sock.recvfrom(1024)
        print('[lpo] received {}-byte packet from {}: {}'.format(
            len(payload), src_addr, payload[:5].hex()))
