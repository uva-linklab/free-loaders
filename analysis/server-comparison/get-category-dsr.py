import argparse
import re

ap = argparse.ArgumentParser(description='log analyzer')
ap.add_argument('log_file', help='Log file to parse')
args = ap.parse_args()

# lax = 0-9, 50-59
# avg = 10-19, 20-29
# strict= 30-39, 40-49

lax_deadlines_met = 0
lax_count = 0
avg_deadlines_met = 0
avg_count = 0
strict_deadlines_met = 0
strict_count = 0
total_deadlines_met = 0
total_count = 0

with open(args.log_file, 'r') as f:
    data = f.read()
    # finished task(offload_id=2998, task_id=21) on executer_id=9. time(ms)=1240.1247024536133, deadline=1752.32, deadline_met=True, energy=1.1566139936447144
    for matches in re.findall('.*offload_id=(\d+).*task_id=(\d+).*deadline_met=(\w+).*', data):
        offload_id = int(matches[0])
        task_id = int(matches[1])
        deadline_met = (matches[2] == "True")

        # only look at first 2000 tasks
        if offload_id < 2000:
            total_count += 1
            if deadline_met:
                total_deadlines_met += 1

            # lax task
            if task_id in range(0,10) or task_id in range(50,60):
                lax_count += 1
                if deadline_met:
                    lax_deadlines_met += 1
            elif task_id in range(10,20) or task_id in range(20,30):
                avg_count += 1
                if deadline_met:
                    avg_deadlines_met += 1
            elif task_id in range(30,40) or task_id in range(40,50):
                strict_count += 1
                if deadline_met:
                    strict_deadlines_met += 1

    print(f'lax dsr = {lax_deadlines_met/lax_count}')
    print(f'avg dsr = {avg_deadlines_met/avg_count}')
    print(f'strict dsr = {strict_deadlines_met/strict_count}')
    print(f'overall dsr = {total_deadlines_met/total_count}')

    print(f'lax count = {lax_count}')
    print(f'avg count = {avg_count}')
    print(f'strict count = {strict_count}')
