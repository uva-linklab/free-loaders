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
from classes.executer import Executer

ap = argparse.ArgumentParser(description='fReeLoaders controller.')
ap.add_argument('-s', '--scheduler', help='Set the scheduler.',
                metavar='SCHEDULER',
                choices=['rl', 'random', 'time-greedy', 'energy-greedy', 'time-wrr', 'energy-wrr', 'load-bal'],
                dest='scheduler', default='rl')
args = ap.parse_args()

print(args.scheduler)


# TODO remove and add to executers.json
executers = {
    0: Executer(0, "172.27.153.31"),  # nano

    1: Executer(1, "172.27.150.233"),  # rpi3
    2: Executer(2, "172.27.134.111"),  # rpi3

    3: Executer(3, "172.27.138.171"),  # rpi4
    4: Executer(4, "172.27.139.169"),  # rpi4
    5: Executer(5, "172.27.129.215"),  # rpi4
    6: Executer(6, "172.27.184.237"),  # rpi4
    7: Executer(7, "172.27.151.135"),  # rpi4

    8: Executer(8, "172.27.130.255"),  # tx2
    9: Executer(9, "172.27.133.131"),  # desktop
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

# start the task dispatcher
task_dispatcher = TaskDispatcher(scheduler, executers)

# start the http server to receive tasks from offloaders
controller_server = ControllerServer(task_dispatcher)
controller_server.start_server()
