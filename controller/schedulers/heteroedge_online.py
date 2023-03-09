class HeteroedgeScheduler:

    def __init__(self, executors):
        self.needs_before_state = False
        self.needs_feedback = False

    def schedule(self, before_state, task):
        print(f'[HE] scheduled task(offload_id={task.offload_id}, job_id={task.job_id}, task_id={task.task_id}) on executer_id={task.schedule_on_executor}')
        return task.schedule_on_executor

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        pass
