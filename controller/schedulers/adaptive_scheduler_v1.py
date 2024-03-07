import queue
# algorithm which tries to outperform RL purely based on balancing the load
#
# - use most capable as the primary.
# - If there are other executors available and not loaded, use them instead of primary.
# - If they can’t do the task, then don’t pick them again.

MAX_NORM_CPU_LOAD = 0.75

class AdaptiveSchedulerV1:
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
        self.state_table = {}
        self.no_of_active_tasks = [0] * self.total_executor
        self.task_executor_candidate = [[True] * self.total_executor for i in range(100)]  # assuming max 100 tasks

    def get_executor_candidate(self, before_state, task):
        cpu_counts = [before_state[str(i)]['cpu-count'] for i in range(0, self.total_executor)]
        cpu_loads = [before_state[str(i)]['cpu-load'] for i in range(0, self.total_executor)]
        normalized_loads = [(i, round((cpu_loads[i] / cpu_counts[i]), 3),) for i in range(0, self.total_executor)]
        print('[load-bal] normalized loads: {}'.format([normalized_loads[eid] for eid in range(0, self.total_executor)]))

        score_tuples = zip(range(self.total_executor), self.scores)
        sorted_score_tuples = sorted(score_tuples, key=lambda device: device[1], reverse=True)

        for score_tuple in sorted_score_tuples:
            executor = score_tuple[0]

            print(f'load of executor {executor} = {before_state[str(executor)]["cpu-load"]}')
            print(f'norm. load of executor {executor} = {normalized_loads[executor][1]}')
            print(f'no. of active tasks on e{executor} = {self.no_of_active_tasks[executor]}')

            # 1. don't schedule if this executor has failed to meet the deadline of this task_id in the past
            # 2. don't schedule more tasks than the no. of available cpus (basic load balancing)
            # 3. don't schedule if 1min avg normalized cpu load is higher than max allowed load (basic load balancing)
            if self.task_executor_candidate[task.task_id][executor]:
                if self.no_of_active_tasks[executor] < cpu_counts[executor]:
                    if normalized_loads[executor][1] < MAX_NORM_CPU_LOAD:
                        return executor
                    else:
                        print(f'executor {executor} cpu load too high: {normalized_loads[executor][1]}')
                else:
                    print(f'executor {executor} has too many tasks running: {self.no_of_active_tasks[executor]}')
            else:
                print(f'executor {executor} has failed to meet t{task.task_id} deadline in the past')

        # if nothing to pick, fall back to device with best score
        return sorted_score_tuples[0][0]

    def schedule(self, before_state, task):
        executor = self.get_executor_candidate(before_state, task)
        self.no_of_active_tasks[executor] += 1
        self.state_table[task.offload_id] = task.deadline
        print(f'[adpt-lb] scheduled task(offload_id={task.offload_id}, task_id={task.task_id}) on executer_id={executor}.')
        return executor

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, task_id, status, exec_time, energy, new_state_of_executor):
        self.no_of_active_tasks[int(exec_id)] -= 1
        print(f'FINISHED. no. of active tasks on e{exec_id} = {self.no_of_active_tasks[int(exec_id)]}')

        # record if we met the deadline for this task or not
        deadline_met = exec_time <= self.state_table[offload_id]
        self.task_executor_candidate[task_id][int(exec_id)] = deadline_met

    def feedback_consumer(self):
        print("[adpt-lb] starting feedback consumer")
        while True:
            item = self.feedback_q.get()

            self.task_finished(item["offload_id"],
                               item["exec_id"],
                               item["task_id"],
                               item["status"],
                               item["exec_time"],
                               item["energy"],
                               item["new_state_of_executor"])

            self.feedback_q.task_done()
