import argparse
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
from classes.executer import Executer

ap = argparse.ArgumentParser(description='fReeLoaders controller.')
ap.add_argument('-s', '--scheduler', help='Set the scheduler.',
                metavar='SCHEDULER',
                choices=['rl', 'random', 'time-greedy', 'energy-greedy', 'time-wrr', 'energy-wrr', 'load-bal',
                         'heteroedge', 'heros', 'adpt-lb-v1', 'adpt-lb-v2', 'adpt-lb-v3'],
                dest='scheduler', default='rl')
args = ap.parse_args()

executers = {
    0: Executer(0, "172.27.153.31"),  # nano

    1: Executer(1, "172.27.133.177"),  # rpi3
    2: Executer(2, "172.27.134.111"),  # rpi3

    3: Executer(3, "172.27.186.208"),  # rpi4 32bd
    4: Executer(4, "172.27.166.35"),  # rpi4 32fa
    5: Executer(5, "172.27.190.174"),  # rpi4 5e16
    6: Executer(6, "172.27.190.243"),  # rpi4 655d
    7: Executer(7, "172.27.184.70"),  # rpi4 a906

    8: Executer(8, "172.27.130.255"),  # tx2
    9: Executer(9, "172.27.156.67"),  # desktop
}

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
task_dispatcher = TaskDispatcher(scheduler, executers)

# start the http server to receive tasks from offloaders
controller_server = ControllerServer(task_dispatcher)
controller_server.start_server()
