import queue
# algorithm which tries to outperform RL purely based on balancing the load
#
# - use most capable as the primary.
# - If there are other executors available and not loaded, use them instead of primary.
# - If they can’t do the task, then don’t pick them again.

MAX_ACTIVE_TASKS = 5
MAX_NORM_CPU_LOAD = 0.75

class AdaptiveScheduler:
    def __init__(self, executors):
        self.executors = executors
        self.total_executor = len(executors.keys())
        self.needs_before_state = True
        self.needs_feedback = True
        self.feedback_q = queue.Queue()

        # score = geekbench score / compute power. higher is better.
        self.scores = [
            635.3383459,  # nano
            155.1401869, 155.1401869,  # rpi3
            285, 285, 285, 285, 285,  # rpi4
            272.5685786,  # tx2
            61.17066291  # desktop
        ]
        self.no_of_active_tasks = [0] * self.total_executor

    def get_executor_candidate(self, before_state):
        cpu_counts = [before_state[str(i)]['cpu-count'] for i in range(0, self.total_executor)]
        cpu_loads = [before_state[str(i)]['cpu-load'] for i in range(0, self.total_executor)]
        normalized_loads = [(i, round((cpu_loads[i] / cpu_counts[i]), 3),) for i in range(0, self.total_executor)]
        print('[load-bal] normalized loads: {}'.format([normalized_loads[eid] for eid in range(0, self.total_executor)]))

        score_tuples = zip(range(self.total_executor), self.scores)
        sorted_score_tuples = sorted(score_tuples, key=lambda device: device[1], reverse=True)

        eid_lowest_load = 0
        lowest_load = 999
        for score_tuple in sorted_score_tuples:
            executor = score_tuple[0]

            print(f'load of executor {executor} = {before_state[str(executor)]["cpu-load"]}')
            print(f'norm. load of executor {executor} = {normalized_loads[executor][1]}')

            print(f'no. of active tasks on e{executor} = {self.no_of_active_tasks[executor]}')

            if self.no_of_active_tasks[executor] < MAX_ACTIVE_TASKS and \
                    normalized_loads[executor][1] < MAX_NORM_CPU_LOAD:
                return executor

            if normalized_loads[executor][1] < lowest_load:
                eid_lowest_load = executor
                lowest_load = normalized_loads[executor][1]

        # if everything is overloaded, then pick the least loaded device
        return eid_lowest_load

    def schedule(self, before_state, task):
        executor = self.get_executor_candidate(before_state)
        self.no_of_active_tasks[executor] += 1
        return executor

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        self.no_of_active_tasks[int(exec_id)] -= 1
        print(f'FINISHED. no. of active tasks on e{exec_id} = {self.no_of_active_tasks[int(exec_id)]}')

    def feedback_consumer(self):
        print("[adpt-lb] starting feedback consumer")
        while True:
            item = self.feedback_q.get()

            self.task_finished(item["offload_id"],
                               item["exec_id"],
                               item["status"],
                               item["exec_time"],
                               item["energy"],
                               item["new_state_of_executor"])

            self.feedback_q.task_done()
