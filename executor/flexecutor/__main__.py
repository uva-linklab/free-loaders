import argparse
import time

import multiprocessing
import multiprocessing.connection
import os
import service
import sys
import threading

import config
import executor
import load
import log
import stats

__Children = {
    'executor': None
}

def main(args):
    # Set the logging level as an environment variable.
    if config.LoggingEnvVar not in os.environ:
        os.environ[config.LoggingEnvVar] = args.log_level

    # Perform boring configuration.
    config.configure_process()

    threading.current_thread().name = 'top'

    cpu_monitor_thread = stats.start_cpu_monitor_thread()
    gpu_monitor_thread = stats.start_gpu_monitor_thread()
    net_monitor_thread = stats.start_net_monitor_thread()
    state_http_server_thread = service.start_state_server(args.unavailable)
    loading_thread = load.start_loading_thread()
    __Children['executor'] = __start_executor(
        args.controller, args.id, args.power, args.log_level, args.unavailable)

    # Idle around.
    while True:
        # Wait for a process to end.
        sentinels = [__Children['executor'].sentinel]
        mp_event = multiprocessing.connection.wait(sentinels)

        if not __Children['executor'].is_alive():
            log.w('executor died')
            __Children['executor'] = __start_executor(
                args.controller, args.id, args.power, args.log_level, args.unavailable)

def __start_executor(controller_addr, executor_id, power, log_level, unavailable):
    log.i('starting executor')
    proc = executor.start_executor(controller_addr, executor_id, power, log_level, unavailable)
    log.i('started executor (PID {})'.format(proc.pid))

    return proc

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='fReeLoaders executor.')
    ap.add_argument('-l', '--log-level', help='Set the logging level.',
                    metavar='LEVEL', choices=['e', 'w', 'i', 'd'],
                    dest='log_level', default='e')
    ap.add_argument('--unavailable', help='Always reject task execution requests.',
                    action='store_true', default=False)
    ap.add_argument('controller', help='Address of the controller.',
                    metavar='ADDR')
    ap.add_argument('id', help='ID the executor should use.',
                    metavar='NUM', type=int)
    ap.add_argument('power', help='Power value used to calculate energy usage sent back after task executions.',
                    metavar='POWER', type=float)

    args = ap.parse_args()

    main(args)
