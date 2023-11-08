import random
class RandomScheduler:

    def __init__(self, executors):
        # remove executors 8 and 9 for adaptability
        #executors.pop(8)
        #executors.pop(9)

        self.executors = executors
        self.total_executor = len(executors.keys())
        self.needs_before_state = False
        self.needs_feedback = False

        # to ensure reproducibility
        SEED = 1677831403
        random.seed(a=SEED)

    def schedule(self, before_state, task):
        executor = random.choice(list(self.executors.keys()))
        print(f'[adpt-lb] scheduled task(offload_id={task.offload_id}, task_id={task.task_id}) on executer_id={executor}.')
        return executor

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        pass
