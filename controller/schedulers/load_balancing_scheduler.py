class LoadBalancingScheduler:

    def __init__(self, executors):
        executors.pop(8)
        executors.pop(9)

        self.executors = executors
        self.total_executor = len(executors.keys())
        self.needs_before_state = True
        self.needs_feedback = False

    def schedule(self, before_state, task):
        cpu_counts = [before_state[str(i)]['cpu-count'] for i in range(0, self.total_executor)]
        cpu_loads = [before_state[str(i)]['cpu-load'] for i in range(0, self.total_executor)]
        normalized_loads = [(i, round((cpu_loads[i] / cpu_counts[i]), 3),) for i in range(0, self.total_executor)]
        print('[load-bal] normalized loads: {}'.format([normalized_loads[eid] for eid in range(0, self.total_executor)]))

        best_eid = 0
        best_load = 999
        for (eid, load) in normalized_loads:
            if load < best_load:
                best_eid = eid
                best_load = load

        print('[load-bal] scheduled task(offload_id={}, task_id={}) on executer_id={}'.format(
            task.offload_id, task.task_id, best_eid))

        return best_eid

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        pass
