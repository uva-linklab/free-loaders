# algorithm which tries to outperform RL purely based on balancing the load
#
# - use most capable as the primary.
# - If there are other executors available and not loaded, use them instead of primary.
# - If they can’t do the task, then don’t pick them again.
class AdaptiveScheduler:

    def __init__(self, executors):
        self.executors = executors
        self.total_executor = len(executors.keys())
        self.needs_before_state = True
        self.needs_feedback = True
        self.primary = None

    def get_primary(self, before_state):
        return 0

    def is_overloaded(self, before_state):
        return 0

    def schedule(self, before_state, task):
        print(before_state)
        if self.primary is None:
            self.primary = self.get_primary(before_state)

        # check if primary is overloaded
        # if self.is_overloaded()
        return 0

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        pass

