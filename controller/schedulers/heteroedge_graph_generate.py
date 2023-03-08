# input: no. of jobs, no. of tasks, energy for each task on each executor
# output: edge_list
def get_edge_list(jobs, executors, tasks, task_executor_energy):
    edge_list = []
    for index, task in enumerate(tasks):
        for executor_id in executors:
            node = f'{task}-e{executor_id}'
            if index == 0:
                for job_id in range(jobs):
                    # create a new start node
                    job_start_node = f"s{job_id}"
                    edge_list.append((job_start_node, node, 0))
            if index == len(tasks) - 1:
                edge_list.append((node, 't', task_executor_energy[(task, executor_id)]))
            else:
                for next_exec_id in executors:
                    next_task = tasks[index+1]
                    next_node = f'{next_task}-e{next_exec_id}'
                    edge_list.append((node, next_node, task_executor_energy[(task, executor_id)]))

    return edge_list

jobs = 2
executors = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
tasks = ["t9", "t19", "t29"]
task_executor_energy = {
    ("t9",0): 2.11,
    ("t9",1): 4.19,
    ("t9",2): 4.19,
    ("t9",3): 3.82,
    ("t9",4): 3.82,
    ("t9",5): 3.82,
    ("t9",6): 3.82,
    ("t9",7): 3.82,
    ("t9",8): 4.92,
    ("t9",9): 24.97,

    ("t19",0): 4.20,
    ("t19",1): 112.43,
    ("t19",2): 112.43,
    ("t19",3): 98.28,
    ("t19",4): 98.28,
    ("t19",5): 98.28,
    ("t19",6): 98.28,
    ("t19",7): 98.28,
    ("t19",8): 10.01,
    ("t19",9): 166.54,

    ("t29",0): 0.29,
    ("t29",1): 1.02,
    ("t29",2): 1.02,
    ("t29",3): 2.28,
    ("t29",4): 2.28,
    ("t29",5): 2.28,
    ("t29",6): 2.28,
    ("t29",7): 2.28,
    ("t29",8): 0.76,
    ("t29",9): 6.68,
}

edge_list = get_edge_list(jobs,executors,tasks,task_executor_energy)
print(edge_list)
print(len(edge_list))