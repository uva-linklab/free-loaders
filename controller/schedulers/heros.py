class Task:
    def __init__(self, ins, memory, gpu):
        self.ins = ins
        self.memory = memory
        self.gpu = gpu

class ExecutorSpecification:
    def __init__(self, max_mips):
        self.max_mips = max_mips

_ExecutorData = {
    0: ExecutorSpecification(3085.06),
    1: ExecutorSpecification(1137.11),
    2: ExecutorSpecification(1137.11),
    3: ExecutorSpecification(2422.04),
    4: ExecutorSpecification(2422.04),
    5: ExecutorSpecification(2422.04),
    6: ExecutorSpecification(2422.04),
    7: ExecutorSpecification(2422.04),
    8: ExecutorSpecification(4140.84),
    9: ExecutorSpecification(15274.47),
}

__TaskData = {
    0: Task(459325960, 7464, None),
    1: Task(886354884, 7376, None),
    2: Task(1313354711, 7496, None),
    3: Task(1740435521, 7380, None),
    4: Task(2167353560, 7376, None),
    5: Task(2594311971, 7488, None),
    6: Task(3021406406, 7460, None),
    7: Task(3448343252, 7484, None),
    8: Task(3875417462, 7484, None),
    9: Task(4302362416, 7500, None),

    10: Task( 4308696059, 37304, None), # 750
    11: Task( 5726251592, 40112, None), # 833
    12: Task( 7454959898, 43776, None), # 916
    13: Task( 9524912292, 47212, None), # 999
    14: Task(11967812230, 51400, None), # 1082
    15: Task(14815489823, 55792, None), # 1165
    16: Task(18056186224, 60536, None), # 1247
    17: Task(21750177333, 65280, None), # 1329
    18: Task(25927403084, 70712, None), # 1411
    19: Task(30619003800, 76336, None), # 1493

    20: Task(459238339, 24024, None), # 2600
    21: Task(461493645, 24604, None), # 2977
    22: Task(462138930, 24620, None), # 3356
    23: Task(462189053, 24484, None), # 3733
    24: Task(462426050, 24600, None), # 4111
    25: Task(460854789, 24412, None), # 4489
    26: Task(462730871, 24316, None), # 5244
    27: Task(460316118, 25056, None), # 5411
    28: Task(463780163, 25072, None), # 5622
    29: Task(460506910, 24372, None), # 6000
}

class HerosScheduler:

    def __init__(self, executors):
        self.executors = executors
        self.total_executor = len(executors.keys())
        self.needs_before_state = True
        self.needs_feedback = False

    def schedule(self, before_state, task):
        # Filter to only those that can handle the task.
        eligible_executors = [it[0] for it in _ExecutorData.items() if executor_is_eligible(it[0], before_state[str(it[0])], task)]
        print('[heros] executors eligible for task_id={}: {}'.format(
            task.task_id, eligible_executors))

        best_h = -999
        best_eid = 0

        print('[heros] selection scores: {}'.format(
            [(eid, '{:.2}'.format(s['h']),) for (eid, s) in before_state.items()]))

        # Use the executor with the greatest H.
        for (eid, state) in before_state.items():
            eid = int(eid)
            # Executor must be eligible.
            if eid not in eligible_executors:
                continue

            if state['h'] > best_h:
                best_eid = eid
                best_h = state['h']

        print('[heros] selecting executor_id={} (h={:.3})'.format(
            best_eid, best_h))

        return best_eid

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        pass

def executor_is_eligible(eid, state, task):
    task_m_ins = __TaskData[task.task_id].ins / 1000000
    est_req_time = task_m_ins / _ExecutorData[eid].max_mips
    print('[heros] est. completion time: {:.2} s'.format(est_req_time))
    cpu_good = est_req_time <= task.deadline

    # Memory usage
    free_ram_kb = state['free-ram'] / 1024
    memory_good = free_ram_kb > __TaskData[task.task_id].memory

    return cpu_good and memory_good
