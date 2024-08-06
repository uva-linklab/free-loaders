"""
choose the best performing executor for a task.
eventually explore feasibility of executing task on less energy consuming executors.
"""
import queue

MAX_NORM_CPU_LOAD = 0.75
MAX_ALLOWED_DEADLINE_MISSES = 5

EXPLORATION_DEADLINE_HIT_THRESHOLD = 10


class AdaptiveSchedulerV3:
    def __init__(self, executors):
        self.executors = executors
        self.total_executors = len(executors.keys())
        self.needs_before_state = True
        self.needs_feedback = True
        self.feedback_q = queue.Queue()

        # score = geekbench score / compute power. higher is better.
        self.geekbench_scores = {
            0: 845,  # nano
            1: 166,  # rpi3
            2: 166,  # rpi3
            3: 513,  # rpi4
            4: 513,  # rpi4
            5: 513,  # rpi4
            6: 513,  # rpi4
            7: 513,  # rpi4
            8: 1093,  # tx2
            9: 4337  # desktop
        }

        # list of executor_id in decreasing order of geekbench scores
        self.ordered_exec_list = list(
            map(lambda x: x[0],
                sorted(self.geekbench_scores.items(),
                       key=lambda tup: tup[1],
                       reverse=True)))

        # stores the current executor for a given task_id
        # default to the most powerful executor (index 0 in self.ordered_exec_list)
        self.current_executor = [0] * 100  # assuming max 100 tasks
        self.is_exploration_allowed = [True] * 100  # assuming max 100 tasks
        self.deadline_hit_count = [0] * 100  # assuming max 100 tasks

        self.deadline_table = {}
        self.temporary_mode = set()
        self.no_of_active_tasks = [0] * self.total_executors
        # self.executor_states = [[ExecutorState.CANDIDATE] * self.total_executors for i in range(100)]  # assuming max 100 tasks
        # self.deadline_miss_count = [[0] * self.total_executors for i in range(100)]  # assuming max 100 tasks

    def get_executor_candidate(self, before_state, task):
        cpu_counts = [before_state[str(i)]['cpu-count'] for i in range(0, self.total_executors)]
        cpu_loads = [before_state[str(i)]['cpu-load'] for i in range(0, self.total_executors)]
        normalized_loads = [(i, round((cpu_loads[i] / cpu_counts[i]), 3),) for i in range(0, self.total_executors)]

        # note: this index is different to task dispatcher's executor_id
        candidate_executor_index = self.current_executor[task.task_id]
        search_downstream = False
        search_upstream = False
        while True:
            candidate_executor = self.ordered_exec_list[candidate_executor_index]

            # boundary conditions when doing search for alternative candidate
            if (search_downstream and candidate_executor_index == self.total_executors - 1) \
                    or \
                    (search_upstream and candidate_executor_index == 0):
                return candidate_executor

            # only schedule on the candidate if they:
            # 1. don't have more tasks than no. of CPUs
            # 2. don't have CPU load >= MAX_NORM_CPU_LOAD
            if self.no_of_active_tasks[candidate_executor] < cpu_counts[candidate_executor]:
                if normalized_loads[candidate_executor][1] < MAX_NORM_CPU_LOAD:
                    return candidate_executor

            # if program reaches here, current candidate cannot be picked due to load
            # to find alternative candidate, decide which direction to search
            # only make this decision if we've not decided the direction already
            if not search_downstream and not search_upstream:
                # note down that this offload should not be counted towards regular scrutiny
                self.temporary_mode.add(task.offload_id)

                # if we can't schedule on the most powerful executor, then look downstream
                if candidate_executor_index == 0:
                    search_downstream = True
                else:
                    search_upstream = True

            if search_downstream:
                candidate_executor_index += 1  # pick a downstream executor
            elif search_upstream:
                candidate_executor_index -= 1  # pick an upstream executor

    def schedule(self, before_state, task):
        executor = self.get_executor_candidate(before_state, task)
        self.no_of_active_tasks[executor] += 1
        self.deadline_table[task.offload_id] = task.deadline
        print(
            f'[adpt-lb] scheduled task(offload_id={task.offload_id}, task_id={task.task_id}) on executer_id={executor}.')
        return executor

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, task_id, status, exec_time, energy, new_state_of_executor):
        self.no_of_active_tasks[int(exec_id)] -= 1

        if offload_id in self.temporary_mode:
            self.temporary_mode.remove(offload_id)
            return

        deadline_met = exec_time <= self.deadline_table[offload_id]
        if deadline_met:
            if self.is_exploration_allowed[task_id]:
                self.deadline_hit_count[task_id] += 1

                if self.deadline_hit_count[task_id] == EXPLORATION_DEADLINE_HIT_THRESHOLD:
                    self.deadline_hit_count[task_id] = 0  # reset the count

                    # if you've reached executor with lowest score, no more exploration possible
                    # ex: reached last rpi3 downstream
                    if self.current_executor[task_id] == self.total_executors - 1:
                        self.is_exploration_allowed[task_id] = False
                    else:
                        self.current_executor[task_id] += 1  # move to the next executor downstream
        else:
            # if you missed a deadline while exploring (i.e., not on the machine with highest score)
            if self.current_executor[task_id] > 0:
                # backtrack and stop further downstream exploration
                self.current_executor[task_id] -= 1
                self.is_exploration_allowed[task_id] = False

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
