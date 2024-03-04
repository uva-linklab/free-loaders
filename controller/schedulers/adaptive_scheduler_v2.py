import queue
# algorithm which tries to outperform RL purely based on balancing the load
#
# - use most capable as the primary.
# - If there are other executors available and not loaded, use them instead of primary.
# - If an executor misses the deadline, temporarily revoke candidacy of executor for 5 mins.
# - Allow maximum of 10 temporary revokes before permanently revoking the candidacy on an executor.
from threading import Timer
from enum import Enum

MAX_NORM_CPU_LOAD = 0.75
MAX_TEMP_REVOKES = 10
TEMP_REVOKE_TIME_SEC = 5 * 60.0

ExecutorState = Enum('ExecutorState', ['CANDIDATE', 'TEMP_BANNED', 'PERM_BANNED'])

class AdaptiveSchedulerV2:
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
        self.executor_states = [[ExecutorState.CANDIDATE] * self.total_executor for i in range(100)]  # assuming max 100 tasks
        self.deadline_miss_count = [[0] * self.total_executor for i in range(100)]  # assuming max 100 tasks

    def get_executor_candidate(self, before_state, task):
        cpu_counts = [before_state[str(i)]['cpu-count'] for i in range(0, self.total_executor)]
        cpu_loads = [before_state[str(i)]['cpu-load'] for i in range(0, self.total_executor)]
        normalized_loads = [(i, round((cpu_loads[i] / cpu_counts[i]), 3),) for i in range(0, self.total_executor)]

        score_tuples = zip(range(self.total_executor), self.scores)
        sorted_score_tuples = sorted(score_tuples, key=lambda device: device[1], reverse=True)

        for score_tuple in sorted_score_tuples:
            executor = score_tuple[0]

            # 1. don't schedule if this not a candidate executor
            # 2. don't schedule more tasks than the no. of available cpus (basic load balancing)
            # 3. don't schedule if 1min avg normalized cpu load is higher than max allowed load (basic load balancing)
            if self.executor_states[task.task_id][executor] == ExecutorState.CANDIDATE:
                if self.no_of_active_tasks[executor] < cpu_counts[executor]:
                    if normalized_loads[executor][1] < MAX_NORM_CPU_LOAD:
                        return executor

        # if nothing to pick, fall back to device with best score
        return sorted_score_tuples[0][0]

    def schedule(self, before_state, task):
        executor = self.get_executor_candidate(before_state, task)
        self.no_of_active_tasks[executor] += 1
        self.state_table[task.offload_id] = task.deadline
        print(f'[adpt-lb] scheduled task(offload_id={task.offload_id}, task_id={task.task_id}) on executer_id={executor}.')
        return executor

    def __temp_revoke_timer_expired__(self, task_id, exec_id):
        # TODO: check if thread-safe
        # make the executor a candidate again, if not permabanned
        if self.executor_states[task_id][int(exec_id)] != ExecutorState.PERM_BANNED:
            self.executor_states[task_id][int(exec_id)] = ExecutorState.CANDIDATE
            print(f'removed temporary revoke of e{exec_id} for task_id={task_id}.')

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, task_id, status, exec_time, energy, new_state_of_executor):
        self.no_of_active_tasks[int(exec_id)] -= 1

        # record a missed deadline for this executor for the task
        deadline_met = exec_time <= self.state_table[offload_id]

        if not deadline_met:
            # self.is_executor_candidate[task_id][int(exec_id)] = False
            self.deadline_miss_count[task_id][int(exec_id)] += 1
            print(f'missed deadline for task_id={task_id}, on e{exec_id} for {self.deadline_miss_count[task_id][int(exec_id)]} times')

            if self.deadline_miss_count[task_id][int(exec_id)] < MAX_TEMP_REVOKES:
                # temporarily ban this executor
                self.executor_states[task_id][int(exec_id)] = ExecutorState.TEMP_BANNED
                print(f'temp revoked candidacy of e{exec_id} for task_id={task_id}')

                # start a timer to remove temporary ban after sometime
                t = Timer(TEMP_REVOKE_TIME_SEC, self.__temp_revoke_timer_expired__, args=[task_id, exec_id])
                t.start()
            else:
                # max temp revokes reached, permanently revoke candidacy
                self.executor_states[task_id][int(exec_id)] = ExecutorState.PERM_BANNED
                print(f'permanently revoked candidacy of e{exec_id} for task_id={task_id}')

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
