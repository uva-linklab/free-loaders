import argparse
import os
import os.path
import sys

import classes.executer
import lpo_server
import slt

from server import ControllerServer
from task_dispatcher import TaskDispatcher
from schedulers.random_scheduler import RandomScheduler
from schedulers.rl_scheduler import RLScheduler
from schedulers.time_greedy_scheduler import TimeGreedyScheduler
from schedulers.energy_greedy_scheduler import EnergyGreedyScheduler
from schedulers.time_wrr_scheduler import TimeWRRScheduler
from schedulers.energy_wrr_scheduler import EnergyWRRScheduler
from schedulers.load_balancing_scheduler import LoadBalancingScheduler
from schedulers.heros import HerosScheduler
from schedulers.heteroedge_online import HeteroedgeScheduler
from schedulers.adaptive_scheduler_v1 import AdaptiveSchedulerV1
from schedulers.adaptive_scheduler_v2 import AdaptiveSchedulerV2
from schedulers.adaptive_scheduler_v3 import AdaptiveSchedulerV3

ap = argparse.ArgumentParser(description='fReeLoaders controller.')
ap.add_argument('-s', '--scheduler', help='Set the scheduler.',
                metavar='SCHEDULER',
                choices=['rl', 'random', 'time-greedy', 'energy-greedy', 'time-wrr', 'energy-wrr', 'load-bal',
                         'heteroedge', 'heros', 'adpt-lb-v1', 'adpt-lb-v2', 'adpt-lb-v3'],
                dest='scheduler', default='rl')
ap.add_argument('-e', '--executor-metadata', help='Path to executor JSON file',
                dest='executor_metadata_path', type=str, default=os.path.join(os.getcwd(), 'executors.json'))
ap.add_argument('--mqtt-broker-ip', help='IP address of the MQTT broker',
                dest='broker_ip', default='localhost')
ap.add_argument('-l', '--enable-load-testing', help='Enable synthetic load testing',
                dest='slt', action='store_true', default=False)
ap.add_argument('--test-load-spec', help='Parse and verify synthetic load specification',
                dest='test_load_spec', action='store_true', default=False)
ap.add_argument('--enable-lpo-server', help='Listen for offloads from low-power offloaders',
                dest='enable_lpo_server', action='store_true', default=False)

args = ap.parse_args()

# Assume that the CWD will always be the top of the repository.
executer_json_path = args.executor_metadata_path
print('[controller] loaded executers from {}'.format(executer_json_path))
executers = classes.executer.from_file(executer_json_path)
executers = { e.executer_id: e for e in executers }

print('[controller] loaded {} executers'.format(len(executers)))
for (eid, executer) in executers.items():
    print('[controller] EID {} at {}'.format(eid, executer.executer_ip))

# Create synthetic load tester.
sl_tester = None
if args.slt == True or args.test_load_spec == True:
    print('[controller] synthetic load testing enabled')
    sl_tester = slt.SyntheticLoadTester(
        os.path.join(os.getcwd(), 'load-spec.json'),
        executers)

# Check of the --test-load-spec flag was given; if so, exit now.
if args.test_load_spec == True:
    print('[controller] testing load spec finished')
    sys.exit(0)

scheduler = None

if args.scheduler == "rl":
    scheduler = RLScheduler(executers)
elif args.scheduler == "random":
    scheduler = RandomScheduler(executers)
elif args.scheduler == "time-greedy":
    scheduler = TimeGreedyScheduler(executers)
elif args.scheduler == "energy-greedy":
    scheduler = EnergyGreedyScheduler(executers)
elif args.scheduler == "time-wrr":
    scheduler = TimeWRRScheduler(executers)
elif args.scheduler == "energy-wrr":
    scheduler = EnergyWRRScheduler(executers)
elif args.scheduler == "load-bal":
    scheduler = LoadBalancingScheduler(executers)
elif args.scheduler == "heros":
    scheduler = HerosScheduler(executers)
elif args.scheduler == "heteroedge":
    scheduler = HeteroedgeScheduler(executers)
elif args.scheduler == "adpt-lb-v1":
    scheduler = AdaptiveSchedulerV1(executers)
elif args.scheduler == "adpt-lb-v2":
    scheduler = AdaptiveSchedulerV2(executers)
elif args.scheduler == "adpt-lb-v3":
    scheduler = AdaptiveSchedulerV3(executers)

print(f'[controller] using {args.scheduler} scheduler')

# start the task dispatcher
task_dispatcher = TaskDispatcher(scheduler, executers, sl_tester, broker_ip=args.broker_ip)

# start the lpo listener
lpo_server_thread = None
if args.enable_lpo_server == True:
    lpo_server_thread = lpo_server.start_server(task_dispatcher)

# start the http server to receive tasks from offloaders
controller_server = ControllerServer(task_dispatcher)
controller_server.start_server()
