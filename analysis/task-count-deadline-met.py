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

task_details = {}

# open log file
with open(args.log_file, 'r') as f:
    data = f.read()
    # finished task(offload_id=262, task_id=21) on executer_id=0. time(ms)=2952.688694000244, deadline=2977.777777777778, deadline_met=True, energy=0.06402182579040527
    # failed task(offload_id=4806, task_id=18) on executer_id=1, status=1. deadline=18694.444444444445, deadline_met=False

    # .*failed task.*task_id=(\d+).*deadline_met=(True|False)
    for matches in re.findall('.*(finished|failed) task.*task_id=(\d+).*deadline_met=(True|False)', data):
        task_id = int(matches[1])
        deadline_met = True if matches[2] == "True" else False

        if task_id not in task_details:
            task_details[task_id] = {
                "count": 0,
                "deadlines_met": 0
            }

        task_details[task_id]["count"] += 1
        task_details[task_id]["deadlines_met"] = task_details[task_id]["deadlines_met"] + 1 if deadline_met else \
            task_details[task_id]["deadlines_met"]

sorted_dict = dict(sorted(task_details.items()))
# print(sorted_dict)

print("TaskId\tCount\tDeadlinesMet\tDeadlinesMissed")
for k, v in sorted_dict.items():
    print(f'{k}\t{v["count"]}\t{v["deadlines_met"]}\t\t{v["count"]-v["deadlines_met"]}')

# print(sorted_mapping)
# devices = ["nano", "rpi3", "rpi3", "rpi4", "rpi4", "rpi4", "rpi4", "rpi4", "tx2", "desktop"]
# devices_with_index = [f'{device}({index})' for (index,device) in enumerate(devices)]
# res = []
# for key, val in sorted_mapping.items():
#     highest_offloaded = max(val)
#     highest_offloaded_index = val.index(highest_offloaded)
#     res.append([key] + val + [devices[highest_offloaded_index] + f"({highest_offloaded_index})"])
#
# # headers = ["TaskId"] + ["Executor" + str(i) for i in range(args.num_executors)]
# headers = ["TaskId"] + devices_with_index + ["MaxOffloaded"]
#
# print(tabulate(res, headers=headers))
