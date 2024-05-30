import argparse
import json
import requests

ExecutorIPs = {
    0: "172.27.153.31",  # nano

    1: "172.27.133.177",  # rpi3
    2: "172.27.134.111",  # rpi3

    3: "172.27.186.208",  # rpi4 32bd
    4: "172.27.166.35",  # rpi4 32fa
    5: "172.27.190.174",  # rpi4 5e16
    6: "172.27.190.243",  # rpi4 655d
    7: "172.27.184.70",  # rpi4 a906

    8: "172.27.130.255",  # tx2
    9: "172.27.156.67",  # desktop
}

def __main():
    ap = argparse.ArgumentParser()

    ap.add_argument('-t', '--target', help='Which executors to target; comma-delimited list',
                    type=str, default='')
    ap.add_argument('load', help='Load specification',
                    type=str)
    args = ap.parse_args()

    obj = {}
    if args.load == 'clear':
        obj['profile'] = 'none'
    else:
        sparts = args.load.split(',')

        if sparts[0] == 'constant':
            obj['profile'] = 'constant'
            obj['target'] = int(sparts[1])
        elif sparts[0] == 'intermittent':
            obj['profile'] = 'intermittent'
            obj['frequency'] = 'frequency'
            obj['duration'] = 'duration'

    payload_json = json.dumps(obj)

    # Send the HTTP request to them.
    targets = list(range(0,10))
    if args.target != '':
        targets = list(map(int, args.target.split(',')))

    for t in targets:
        print('Sending update to {}'.format(ExecutorIPs[t]))
        url = 'http://{}:{}/load/set/{}'.format(
            ExecutorIPs[t],
            8088,
            obj['profile'])
        requests.post(url,
                      data=payload_json,
                      headers={'Content-Type: application/json'})

if __name__ == '__main__':
    __main()
