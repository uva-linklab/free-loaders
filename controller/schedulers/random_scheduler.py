import random
class RandomScheduler:

    def __init__(self, executors):
        self.executors = executors
        self.total_executor = len(executors.keys())
        self.needs_before_state = False
        self.needs_feedback = False

    def schedule(self, before_state, task):
        return random.choice(list(self.executors.keys()))

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        pass
