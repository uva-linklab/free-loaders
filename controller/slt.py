import itertools
import requests

__ExecutorCycle = itertools.cycle([[3, 4, 5], [6, 7]])
__LoadSpec = {(x * 100): next(__ExecutorCycle) for x in range(1, 20)}
__LoadSpec[0] = [6, 7]

def update_load(offload_id, executors):
    '''Update artificial load on executor devices.
    '''

    if offload_id in __LoadSpec.keys():
        # Clear the load on all of them.
        for (eid, executor) in executors:
            url = 'http://{}:8088/load/clear'.format(executor.executer_ip)
            requests.post(url)

        # Set the load on the specified executors.
        load_eids = next(__ExecutorCycle)
        for eid in load_eids:
            executor = executors[eid]
            url = 'http://{}:8088/load/set/constant'.format(executor.executer_ip)
            requests.post(url, json={ 'load': 1.0 })
