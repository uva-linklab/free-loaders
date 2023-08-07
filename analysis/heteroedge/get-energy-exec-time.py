# given a log file and a task_id, get the offload_id and energy_consumption
import argparse
import re

ap = argparse.ArgumentParser(description='log analyzer')
ap.add_argument('log_file', help='Log file to parse')
args = ap.parse_args()

total_time = 0.0
total_energy = 0.0

with open(args.log_file, 'r') as f:
    data = f.read()
    for matches in re.findall('.*finished task.*time\(ms\)=(\d+\.\d+).*energy=(\d+\.\d+)', data):
        exec_time = float(matches[0])
        energy = float(matches[1])

        total_energy += energy
        total_time += exec_time

print(f'energy={total_energy}')
print(f'exec_time={total_time}')