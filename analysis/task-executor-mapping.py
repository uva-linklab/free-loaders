# given the log file, extract task id -> list of number of offloads on each executor
import argparse
import re
from tabulate import tabulate

ap = argparse.ArgumentParser(description='log analyzer')
ap.add_argument('-e', '--executor-count', help='specify no. of executors',
                type=int, default=10, dest='num_executors')
ap.add_argument('-es', '--epsilon-start', help='starting epsilon value',
                type=float, default=0.0, dest='epsilon_start')
ap.add_argument('-ee', '--epsilon-end', help='ending epsilon value',
                type=float, default=1.0, dest='epsilon_end')
ap.add_argument('-ois', '--offload-id-start', help='starting offload_id',
                type=int, default=0, dest='start_offload_id')
ap.add_argument('-oie', '--offload-id-end', help='ending offload_id',
                type=int, default=500000, dest='end_offload_id') # setting default end offload to a large number
ap.add_argument('log_file', help='Log file to parse')
args = ap.parse_args()

task_to_executor_mapping = {}  # {0: [5, 2, ...],.. }

# open log file
with open(args.log_file, 'r') as f:
    data = f.read()
    for matches in re.findall('.*scheduled task.*offload_id=(\d+).*task_id=(\d+).*executer_id=(\d+).*epsilon=(\d+\.\d+)', data):
        offload_id = int(matches[0])
        task_id = int(matches[1])
        executor_id = int(matches[2])
        epsilon = float(matches[3])

        if args.start_offload_id <= offload_id <= args.end_offload_id:
            if args.epsilon_start <= epsilon <= args.epsilon_end:
                if task_id not in task_to_executor_mapping:
                    task_to_executor_mapping[task_id] = [0] * args.num_executors

                task_to_executor_mapping[task_id][executor_id] = task_to_executor_mapping[task_id][executor_id] + 1

sorted_mapping = dict(sorted(task_to_executor_mapping.items()))
# print(sorted_mapping)

res = []
for key, val in sorted_mapping.items():
    res.append([key] + val + [sum(val)])

# headers = ["TaskId"] + ["Executor" + str(i) for i in range(args.num_executors)]
headers = ["TaskId"] + ["nano", "rpi3", "rpi3", "rpi4", "rpi4", "rpi4", "rpi4", "rpi4", "tx2", "desktop", "total"]

print(tabulate(res, headers=headers))