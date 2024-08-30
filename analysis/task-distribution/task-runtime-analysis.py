import argparse
import re
import statistics
from tabulate import tabulate

ap = argparse.ArgumentParser(description='Task run-time analyzer')
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

ap.add_argument('dataset', help='dataset to calculate',
                type=str, choices=['runtime', 'runtime-full', 'slack', 'slack-full'],
                dest='dataset')
ap.add_argument('log_file', help='Log file to parse')

args = ap.parse_args()

# TID -> (EID -> [slack times])
task_to_executor_mapping = {}

# open log file
regexp = '.*finished task.*task_id=(?P<tid>\d+).*executer_id=(?P<eid>\d+).*time\(ms\)=(?P<t>\d+|\d+\.\d+).*deadline=(?P<dl>\d+|\d+\.\d+)'
with open(args.log_file, 'r') as f:
    data = f.read()
    for m in re.findall(regexp, data):
        eid = int(m[1])
        tid = int(m[0])
        t_exec = float(m[2])
        t_dl = float(m[3])

        task_slack_times = task_to_executor_mapping.get(tid, {x: [] for x in range(0, 10)})
        ex_slack_times = task_slack_times.get(eid, [])

        if args.dataset.startswith('runtime'):
            ex_slack_times.append(round(t_exec, 1))
        elif args.dataset.startswith('slack'):
            ex_slack_times.append(round(t_dl - t_exec, 1))

        task_slack_times[eid] = ex_slack_times
        task_to_executor_mapping[tid] = task_slack_times

# Transform slack times to average slack time.
rows = []
for (tid, eid_slack_times) in task_to_executor_mapping.items():
    row = [tid]
    for (eid, slack_times) in eid_slack_times.items():
        if len(slack_times) == 0:
            row.append('---')
        else:
            row.append(round(sum(slack_times) / len(slack_times), 2))

    rows.append(row)

rows.sort(key=lambda r: r[0])

devices = ["nano", "rpi3", "rpi3", "rpi4", "rpi4", "rpi4", "rpi4", "rpi4", "tx2", "desktop"]
headers = ["TaskId"] + devices

print('Task running times per executor')
print(tabulate(rows, headers=headers, numalign='decimals'))
