import itertools
import json
import math
import random
import requests

def _log(s):
    print('[slt] {}'.format(s))

class LoadDefinition:
    def __init__(self,
                 executer,
                 represented_duration_hours,
                 total_offload_count,
                 task_rate,
                 load_definition,
                 load_id=None):
        '''Create a load definition.
        '''

        # Executer ID.
        self.__executer = executer
        # The dictionary holding the information about the load.
        self.load_definition = load_definition
        # Parameters necessary for calculating timing.
        self.__represented_duration_hours = represented_duration_hours
        self.__total_offload_count = total_offload_count
        self.__task_rate = task_rate

        # A unique ID to refer to a load.
        # In the context of a clear command, it identifies the load it is clearing.
        self.__load_id = load_id
        if load_id == None:
            self.__load_id = random.randint(1, pow(2, 64))

    def lid(self):
        return self.__load_id

    def eid(self):
        return self.__executer.executer_id

    def request_data(self):
        '''Return (URL, JSON payload) for the load in this definition.
        '''

        load_type = self.load_definition['type']
        parameters = self.load_definition['parameters']

        if load_type == 'constant':
            load_target = parameters['load']

            url = 'http://{}:8088/load/set/constant'.format(
                self.__executer.executer_ip)
            json_payload = { 'load': load_target }

            return (url, json_payload,)

        elif load_type == 'intermittent':
            # Scale the period to the duration of the test.
            period_frac = (parameters['d_period_mins'] / 60 / self.__represented_duration_hours)
            # Convert represented test time to the actual test time.
            actual_test_time_seconds = self.__total_offload_count / self.__task_rate * 60
            # And get the period in seconds for the executore based on the fractional calculation.
            period_seconds = actual_test_time_seconds * period_frac

            # Same as above, but we already have the actual test time.
            duration_frac = (parameters['d_load_mins'] / 60 / self.__represented_duration_hours)
            duration_seconds = actual_test_time_seconds * duration_frac

            url = 'http://{}:8088/load/set/intermittent'.format(
                self.__executer.executer_ip)
            json_payload = { 'load': parameters['load'],
                             'frequency': period_seconds,
                             'duration': duration_seconds, }
            return (url, json_payload,)

        elif load_type == 'clear':
            url = 'http://{}:8088/load/clear'.format(self.__executer.executer_ip)
            json_payload = {}

            return (url, json_payload,)

        else:
            raise Exception('Unknown load request: {}'.format(load_type))

class SyntheticLoadTester:
    def __init__(self, load_spec_path, executers):
        self.__executers = executers
        self.__active_loads = {}

        j = None
        with open(load_spec_path, 'r') as fh:
            j = json.load(fh)

        # Read some global properties of the load specification.
        self.__total_offload_count = j['total_offload_count']
        self.__represented_duration_hours = j['represented_duration_hrs']
        self.__task_rate = j['tasks_per_minute']
        _log('expected offloads: {} tasks, represented duration: {} hrs., expected rate: {} tpm'.format(
            self.__total_offload_count, self.__represented_duration_hours, self.__task_rate))

        self.__timeline = []
        self.__build_load_timeline(j)

    def __build_load_timeline(self, load_spec_json):
        '''Construct the timeline which dictates when to apply and remove loads.
        '''

        import classes.executer
        import os
        import os.path
        executers = classes.executer.from_file(
            os.path.join(os.getcwd(), 'executers.json'))
        executers = { e.executer_id: e for e in executers }

        for (eid, load_specs) in load_spec_json['executor_load_specs'].items():
            _log('found spec for EID {}'.format(eid))

            # The ID is actually a string in JSON to fit dictionary
            eid = int(eid)

            for spec in load_specs:
                # Convert load timing to offload IDs.
                start_min = spec['t_start_min']
                duration_mins = spec['t_duration_mins']

                oid_start = _map_to_offload_id(
                    self.__total_offload_count,
                    self.__represented_duration_hours,
                    start_min)
                oid_end = _map_to_offload_id(
                    self.__total_offload_count,
                    self.__represented_duration_hours,
                    start_min + duration_mins)

                # Add these points to the timeline.
                s_def = LoadDefinition(executers[eid],
                                       self.__represented_duration_hours,
                                       self.__total_offload_count,
                                       self.__task_rate,
                                       spec['load_definition'])
                e_def = LoadDefinition(executers[eid],
                                       self.__represented_duration_hours,
                                       self.__total_offload_count,
                                       self.__task_rate,
                                       { 'type': 'clear',
                                         'parameters': {  } },
                                       load_id=s_def.lid())

                _log('eid: {}, from ({} -> {}): spec: {}'.format(
                    eid, oid_start, oid_end, spec['load_definition']))

                self.__timeline.append((oid_start, s_def,))
                self.__timeline.append((oid_end, e_def,))

        # Sort the timeline.
        def ___rank_timeline_entry(e):
            # Make clear operations appear before other ops. in the timeline.
            r = 1
            if 'clear' in e[1].load_definition.keys():
                r = 0

            return (e[0], r,)

        self.__timeline.sort(key=___rank_timeline_entry)

        self.__test_timeline()

    def update_load(self, offload_id, dry_run=False):
        '''Update the synthetic load according to the current offload ID.
        '''

        def ___into_requests_and_data(t):
            return (t[1].eid(), t[1].lid(), t[1].request_data(),)

        real_offload_id = offload_id
        offload_id = offload_id % self.__total_offload_count

        # Issue clear requests if this is the first offload of the timeline.
        if offload_id == 0 and not dry_run:
            import time
            self.clear_synthetic_load()
            time.sleep(1.0)

        # t = (oid, LoadDefinition)
        it = filter(lambda t: t[0] == offload_id, self.__timeline)
        it = map(___into_requests_and_data, it)
        all_requests = list(it)

        if len(all_requests) == 0:
            return

        _log('updating load at offload_id={} (as={})'.format(real_offload_id, offload_id))

        # Make sure clear operations occur first.
        # (eid, lid, (url, json,),)
        all_requests.sort(key=lambda t: 0 if 'clear' in t[2][0] else 1)

        # Find out which executor and load the clear ops. are applying to.
        # We must re-apply the untargeted loads afterward.
        clear_requests = list(filter(lambda t: 'clear' in t[2][0], all_requests))
        for clear_request in clear_requests:
            # Take out the matching ID from the active loads of the executor it targets.
            eid = clear_request[0]
            clear_lid = clear_request[1]
            remaining_active = list(filter(lambda ld: ld.lid() != clear_lid,
                                           self.__active_loads.get(eid, [])))
            # Remove the corresponding load from the active load set.
            self.__active_loads[eid] = remaining_active
            # Create requests to reapply those that should still be active.
            reapply_requests = list(map(lambda ld: (ld.eid(), ld.lid(), ld.request_data(),), remaining_active))
            # They must be placed directly after the clear in the list.
            it = zip(itertools.count(), all_requests)
            clear_request_idx = next(filter(lambda t: t[1][1] == clear_lid, it))[0]
            all_requests = all_requests[0:clear_request_idx+1] + reapply_requests + all_requests[clear_request_idx+1:]

        for (eid, lid, (url, j,),) in all_requests:
            if 'clear' not in url:
                active_load_definition = self.__find_in_timeline(lid)
                self.__add_to_active_loads(active_load_definition)

            if dry_run == True:
                _log('at offload_id={}, apply LID {}: {} to eid={}'.format(
                    offload_id, lid, url, eid))
            else:
                try:
                    requests.post(url, json=j)
                except:
                    pass

        _log('active loads at offload_id={}:'.format(offload_id))
        for (eid, active_loads) in self.__active_loads.items():
            _log('  EID {} -> {}'.format(eid, list(map(lambda ld: ld.lid(), active_loads))))

    def hook_task_finished(self, offload_id):
        '''Hook function to be called when a task is finished.
        '''

        pass

    def clear_synthetic_load(self):
        _log('clearing all synthetic load')
        for executer in self.__executers.values():
            url = 'http://{}:8088/load/clear'.format(executer.executer_ip)
            try:
                requests.post(url, json={})
            except:
                pass

    def __add_to_active_loads(self, load_definition):
        '''Add a load definition to the active loads if it is not already there.
        '''

        l = list(filter(lambda ld: ld.lid() == load_definition.lid(),
                        self.__active_loads.get(load_definition.eid(), [])))
        if len(l) == 0:
            currently_active_loads = self.__active_loads.get(load_definition.eid(), [])
            currently_active_loads.append(load_definition)
            self.__active_loads[load_definition.eid()] = currently_active_loads

    def __find_in_timeline(self, lid):
        '''Retrieve the non-clearing load definition with the LID.
        '''

        t = next(filter(lambda t: t[1].lid() == lid, self.__timeline))
        return t[1]

    def __test_timeline(self):
        _log('testing SLT timeline...')
        for oid in range(0, self.__total_offload_count):
            self.update_load(oid, dry_run=True)

def _map_to_offload_id(total_offloads,
                        represented_duration_hours,
                        t_at_min):
    '''Convert an instant to a corresponding offload ID.
    '''

    t_at_hrs = t_at_min / 60
    frac = t_at_hrs / represented_duration_hours
    offload_id = math.floor(total_offloads * frac)

    return offload_id
