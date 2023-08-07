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
            [(eid, s['h'],) for (eid, s) in before_state.items()]))

        # Use the executor with the greatest H.
        for (eid, state) in before_state.items():
            eid = int(eid)
            # Executor must be eligible.
            if eid not in eligible_executors:
                continue

            if state['h'] > best_h:
                best_eid = eid
                best_h = state['h']

        print('[heros] selecting executor_id={} (h={})'.format(
            best_eid, best_h))

        return best_eid

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        pass

def executor_is_eligible(eid, state, task):
    task_m_ins = __TaskData[task.task_id].ins / 1000000
    est_req_time = task_m_ins / _ExecutorData[eid].max_mips
    cpu_good = est_req_time <= task.deadline

    # Memory usage
    memory_good = state['free-ram'] > __TaskData[task.task_id].memory

    return cpu_good and memory_good
