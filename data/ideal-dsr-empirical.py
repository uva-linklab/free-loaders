import argparse
import re

ap = argparse.ArgumentParser()
ap.add_argument('-s', '--start', help='Offload ID to start inspecting at',
                type=int, default=0, dest='start_id')
ap.add_argument('path', help='path to log file', type=str)

args = ap.parse_args()

log_lines = ''
with open(args.path, 'r') as fh:
    log_lines = fh.readlines()

# Find task IDs where the deadline has been met.
met_tasks = set()
rgx_finished_task = 'finished task\(offload_id=(?P<oid>\d+), task_id=(?P<tid>\d+).*on executer_id=(?P<eid>\d+).*time\(ms\)=(?P<time>\d+\.\d+).*deadline=(?P<dl>\d+\.\d+)'
for line in log_lines:
    m = re.search(rgx_finished_task, line)
    if m == None:
        continue

    oid = int(m['oid'])
    if oid < args.start_id:
        continue

    t = float(m['time'])
    dl = float(m['dl'])

    if t <= dl:
        met_tasks.add(int(m['tid']))

# Generate a set of all task IDs.
all_ids = set([i for i in range(0, 30)])
unattainable = all_ids - met_tasks

print('Cannot meet deadline for {} tasks:\n{}'.format(len(unattainable), unattainable))

ideal_dsr = (len(all_ids) - len(unattainable)) / len(all_ids)
print('Ideal DSR = {}'.format(ideal_dsr))
