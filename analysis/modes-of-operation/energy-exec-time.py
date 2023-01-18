# given a log file and a task_id, get the offload_id and energy_consumption
import argparse
import re

def get_epsilon_zero_offload_id(log_file_path):
    with open(log_file_path, 'r') as f:
        data = f.read()
        for matches in re.findall('.*scheduled task.*offload_id=(\d+).*epsilon=(.*), total_step.*', data):
            offload_id = int(matches[0])
            epsilon = float(matches[1])
            if epsilon <= 0.0:
                return offload_id

ap = argparse.ArgumentParser(description='log analyzer')
ap.add_argument('-tid', '--task-id', help='task_id', type=int, dest='task_id')
ap.add_argument('log_file', help='Log file to parse')
args = ap.parse_args()

epsilon_zero_offload_id = get_epsilon_zero_offload_id(args.log_file)
# print(f'epsilon_zero_offload_id={epsilon_zero_offload_id}')
offload_id_vals_mapping = {}  # {0: [5, 2, ...],.. }

# open log file
with open(args.log_file, 'r') as f:
    data = f.read()
    for matches in re.findall('.*finished task.*offload_id=(\d+).*task_id=(\d+).*time\(ms\)=(\d+\.\d+).*energy=(\d+\.\d+)', data):
        offload_id = int(matches[0])
        task_id = int(matches[1])
        exec_time = float(matches[2])
        energy = float(matches[3])

        if offload_id >= epsilon_zero_offload_id and args.task_id == task_id:
            if task_id not in offload_id_vals_mapping:
                offload_id_vals_mapping[task_id] = [(offload_id, exec_time, energy)]
            else:
                offload_id_vals_mapping[task_id].append((offload_id, exec_time, energy))

time_vals = list(map((lambda a: a[1]), offload_id_vals_mapping[args.task_id]))
avg_time = sum(time_vals) / len(time_vals)

energy_vals = list(map((lambda a: a[2]), offload_id_vals_mapping[args.task_id]))
avg_energy = sum(energy_vals) / len(energy_vals)

# print(f'no. of offloads, avg_time(ms), avg_energy')
print(f'{len(time_vals)}, {avg_time}, {avg_energy}')