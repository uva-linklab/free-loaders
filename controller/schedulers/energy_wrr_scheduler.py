class EnergyWRRScheduler:
    '''Assigns tasks in a weighted round-robin fashion based on executor energy efficiency.
    '''
    def __init__(self, executors):
        self.executors = executors
        self.total_executor = len(executors.keys())
        self.needs_before_state = False
        self.needs_feedback = False

        # Hard-code the active power of the executor hardware.
        self.__active_power = [
            # Jetson Nano
            3.89,
            # RPi 3
            2.5, 2.5,
            # RPi 4
            5.03, 5.03, 5.03, 5.03, 5.03,
            # Jetson TX2
            5.73,
            # Server
            109.6
        ]

        # Determine the max no. of offloads relative to the most power-hungry executor.
        self.__max_assigned = [max(self.__active_power) / self.__active_power[i] for i in range(0, 10)]
        self.__assigned = [0 for _i in range(0, 10)]
        self.__current_bucket_idx = 0

    def schedule(self, before_state, task):
        # Increment the current bucket by one.
        # If that bucket exceeds the count it should have allocated in one round, move on to the next executor.
        current = self.__current_bucket_idx
        self.__assigned[current] += 1
        if self.__assigned[current] >= self.__max_assigned[current]:
            self.__assigned[current] -= self.__max_assigned[current]
            self.__current_bucket_idx = (self.__current_bucket_idx + 1) % self.total_executor

        print('[energy-wrr] scheduled task(offload_id={}, task_id={}) on executer_id={}'.format(
            task.offload_id, task.task_id, current))

        return current

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        pass
