class TimeWRRScheduler:
    '''Assigns tasks in a weighted round-robin fashion based on executor compute capability.

    Uses the Geekbench scores to determine how many tasks each executor gets before moving on to the next exeuctor.
    '''
    def __init__(self, executors):
        self.executors = executors
        self.total_executor = len(executors.keys())
        self.needs_before_state = False
        self.needs_feedback = False

        # Hard-code the Geekbench scores of the executor hardware.
        self.__geekbench_scores = [
            # Jetson Nano
            845,
            # RPi 3
            166, 166,
            # RPi 4
            513, 513, 513, 513, 513,
            # Jetson TX2
            1093,
            # Server
            4337
        ]

        # Create buckets to fill as we assign tasks in a round-robin fashion.
        self.__weight_bucket = [0 for _i in range(0, 10)]
        self.__increment = min(self.__geekbench_scores)
        self.__current_bucket_idx = 0

    def schedule(self, before_state, task):
        current = self.__current_bucket_idx

        # Increase the current bucket's allocation.
        # Move to the next bucket if this task assignment fills the current bucket.
        self.__weight_bucket[current] += self.__increment
        if self.__weight_bucket[current] >= self.__geekbench_scores[current]:
            self.__weight_bucket[current] -= self.__geekbench_scores[current]
            self.__current_bucket_idx = (self.__current_bucket_idx + 1) % self.total_executor

        print('[time-wrr] scheduled task(offload_id={}, task_id={}) on executer_id={}'.format(
            task.offload_id, task.task_id, current))
        return current

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        pass
