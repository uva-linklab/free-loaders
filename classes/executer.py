class Executer:
    def __init__(self, executer_id, executer_ip):
        self.executer_id = executer_id
        self.executer_ip = executer_ip

def from_file(path):
    '''Load executer data from a JSON file at `path`.
    '''

    e = []
    with open(path, 'r') as fh:
        import json
        j_arr = json.load(fh)
        it = map(lambda o: Executer(o['id'], o['ip_address']), j_arr)

        e.extend(it)

    return e
