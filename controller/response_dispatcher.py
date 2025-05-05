import socket
import threading
import queue

def start():
    '''Starts the response dispatch thread.

    Returns: Tuple(response dispatcher thread handle, response queue)
    '''

    response_queue = queue.Queue()

    t = threading.Thread(name='response-dispatcher',
                         target=_response_dispatcher_entry,
                         args=(response_queue,))
    t.start()

    return (t, response_queue)


def _response_dispatcher_entry(response_queue):
    '''Entry point for the response dispatcher thread.
    '''

    print('[rd] started')

    # Response UDP socket setup.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print('[rd] obtained response-sending socket')

    while True:
        r = response_queue.get()
        print(f"[rd] handling response for {r['task_id']}")

        if task_id == 62:
            sock.sendto(r['result'], ('192.168.86.37', 12123,))
            print(f"[rd] sent response for {r['task_id']}")
