import queue
import threading
import time

class Task:
    def __init__(self, ins, memory):
        self.ins = ins
        self.memory = memory

class ExecutorSpecification:
    def __init__(self, max_mips, device):
        self.max_mips = max_mips
        self.device = device

class HerosScheduler:

    def __init__(self, executors, per_task_executor_bandwidth=False, task_data=None):
        self.executors = executors
        self.total_executor = len(executors.keys())
        self.needs_before_state = True
        self.needs_feedback = False

        if task_data == None:
            self._task_data = _TaskData
        else:
            self._task_data = task_data

        self._use_per_executor_task_bandwidth = per_task_executor_bandwidth

    def schedule(self, before_state, task):
        # Filter to only those that can handle the task.
        eligible_executors = []
        est_runtimes_ms = {}
        for (eid, exec_spec) in _ExecutorData.items():
            # See if the executor is defined in the dictionary in controller.py.
            is_online = str(eid) in before_state.keys()
            if not is_online:
                continue

            (is_eligible, est_time_ms,) = self.executor_is_eligible(eid, before_state[str(eid)], task)
            #print('{} is online? {}, is eligible? {}'.format(eid, is_online, is_eligible))
            est_runtimes_ms[eid] = est_time_ms
            if is_eligible:
                eligible_executors.append(eid)

        print('[heros] executors eligible for task_id={}: {}'.format(
            task.task_id, eligible_executors))

        best_h = -999999
        best_eid = 0

        print('[heros] CPU load values:  {}'.format(
            [(eid, '{:.2f}'.format(s['cpu-load']),) for (eid, s) in before_state.items()]))
        print('[heros] selection scores: {}'.format(
            [(eid, '{:.2f}'.format(s['h']),) for (eid, s) in before_state.items()]))

        # Use the executor with the greatest H.
        for (eid, state) in before_state.items():
            eid = int(eid)
            # Executor must be eligible.
            if eid not in eligible_executors:
                continue

            if state['h'] > best_h:
                best_eid = eid
                best_h = state['h']

        print(f'[heros] scheduled task(offload_id={task.offload_id}, task_id={task.task_id}) ' +
              f'on executer_id={best_eid}, h={round(best_h, 2)}, est_time={est_runtimes_ms[best_eid]}.')

        return best_eid

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, task_id, status, exec_time, energy, new_state_of_executor):
        pass

    def executor_is_eligible(self, eid, state, task):
        executor_data = _ExecutorData[eid]

        task_type_id = int(task.task_id / 10) # 0 = loop, 1 = matrix mult., 2 = FFT, ...

        task_m_ins = self._task_data[executor_data.device][task.task_id].ins / 1000000
        est_computation_time_ms = task_m_ins / _ExecutorData[eid].max_mips * 1000

        # Estimate network time.
        est_network_time_ms = None
        if self._use_per_executor_task_bandwidth:
            task_bw = _TaskBandwidthData[task.task_id][eid]
            if task_bw == 0: # Task has never successfully completed on the executor.
                return (False, 99999.9)
            est_network_time_ms = (_TaskSizeData[task.task_id] / 1000.0 * 8.0 / task_bw) * 1000
        else:
            link_capacity_free_Bps = (state['link-capacity-mbits'] * 1000000 / 8) - (state['link-load-bits'] / 8)
            est_network_time_ms = (len(task.input_data) / link_capacity_free_Bps)

        # Estimated required time in milliseconds.
        est_time_ms = est_computation_time_ms + est_network_time_ms

        # Computation
        cpu_good = est_time_ms <= task.deadline

        # Memory usage
        free_ram_kb = state['free-ram'] / 1024
        memory_good = free_ram_kb > self._task_data[executor_data.device][task.task_id].memory

        return (cpu_good and memory_good, est_time_ms,)

class HerosInSituScheduler:

    def __init__(self, executors, per_task_executor_bandwidth=False):

        self.needs_before_state = True
        self.needs_feedback = False

        # Get task data set up like the pre-filled dictionary.
        self._task_data = { arch: {} for arch in _TaskData.keys() }
        self._profile_requests = queue.Queue()
        self._profiling_thread = threading.Thread(name='heros-ondemand-profiler',
                                                  target=HerosInSituScheduler._on_demand_profiler_entry,
                                                  args=(executors, self._task_data, self._profile_requests,))
        self._profiling_thread.start()

        self._heros = HerosScheduler(executors, per_task_executor_bandwidth, self._task_data)

    def schedule(self, before_state, task):

        # Check internal task data for the task ID being requested.
        # If it does not exist, it must be profiled.
        if task.task_id in self._task_data.keys():
            print('[heros-is] task ID {} is profiled; invoking HEROS'.format(task.task_id))
            return self._heros.schedule(before_state, task)
        else:
            # Schedule to the most powerful executor (EID 9).
            # Send a profiling request to the profiler.
            print('[heros-is] task ID {} not yet profiled; enqueueing...'.format(task.task_id))
            self._profile_requests.put(task.task_id)

            return 9

    def _on_demand_profiler_entry(executors, task_data, profile_requests):
        '''Entry for on-demand profiling thread.
        '''

        import requests
        import requests.exceptions

        print('[heros-is-profiler] started')

        # Only need one executor of each type.
        executors = [executors[0],
                     executors[1],
                     executors[3],
                     executors[8],
                     executors[9]]
        archs = [
            'aarch64-nano',
            'aarch64-rpi3',
            'aarch64-rpi4',
            'aarch64-tx2',
            'x86_64-pc',
        ]

        # Which tasks have been profiled.
        profiled_task_ids = []

        # Clear profiling data on all executors.
        print('[heros-is-profiler] clearing profiling data')
        for e in executors:
            url = 'http://{}:8088/profile/clear'.format(e.executer_ip)
            try:
                resp = requests.post(url)
                print('[heros-is-profiler] {} says {}'.format(resp.status_code))
            except requests.exceptions.ConnectionError:
                pass

        print('[heros-is-profiler] done clearing profiling data')

        profiling_waits = 0
        while True:
            task_id = profile_requests.get()
            if task_id in profiled_task_ids:
                continue

            print('[heros-is-profiler] starting profiling for task {}'.format(task_id))

            # Launch profiling on each executor.
            profile_url = 'http://{}:8088/profile/{}'.format(e.executer_ip, task_id)
            for e in executors:
                try:
                    resp = requests.get(profile_url)
                except requests.exceptions.ConnectionError:
                    pass

            time.sleep(1)

            # Get data back from each executor.
            # Continue this loop until we have data for all architectures.
            profiled = []
            while True:
                print('[heros-is-profiler] fetching profiling for task {}'.format(task_id))
                print('[heros-is-profiler] done: {}'.format(profiled))

                for (e, arch) in zip(executors, archs):
                    if arch in profiled:
                        continue

                    profile_url = 'http://{}:8088/profile/{}'.format(e.executer_ip, task_id)
                    try:
                        resp = requests.get(profile_url)
                        if resp.status_code == 200:
                            print('[heros-is-profiler] got profile for arch. {}'.format(arch))
                            rjd = resp.json()
                            task_data[arch][task_id] = Task(rjd['ins_count'], 0) # Don't care about memory usage.
                            profiled.append(arch)
                    except requests.exceptions.ConnectionError:
                        print('[heros-is-profiler] arch. {} not done'.format(arch))
                        # Don't try profiling forever.
                        if profiling_waits >= 15:
                            print('[heros-is-profiler] task {} not possible for {}'.format(task_id, arch))
                            task_data[arch][task_id] = Task(999999999999, 999999999999)
                            profiled.append(arch)

                if len(profiled) == len(task_data.keys()):
                    break

                time.sleep(1)
                profiling_waits += 1

            # Track profiled task IDs.
            profiled_task_ids.append(task_id)

_ExecutorData = {
    0: ExecutorSpecification(2560.35, 'aarch64-nano'),
    1: ExecutorSpecification(1140.61, 'aarch64-rpi3'),
    2: ExecutorSpecification(1140.61, 'aarch64-rpi3'),
    3: ExecutorSpecification(4059.44, 'aarch64-rpi4'),
    4: ExecutorSpecification(4059.44, 'aarch64-rpi4'),
    5: ExecutorSpecification(4059.44, 'aarch64-rpi4'),
    6: ExecutorSpecification(4059.44, 'aarch64-rpi4'),
    7: ExecutorSpecification(4059.44, 'aarch64-rpi4'),
    8: ExecutorSpecification(3876.54, 'aarch64-tx2'),
    9: ExecutorSpecification(13187.94, 'x86_64-pc'),
}

_TaskData = {
    'aarch64-nano': {
        0: Task(83951653, 8776),
        1: Task(686149436, 8712),
        2: Task(1288449451, 8712),
        3: Task(1890842570, 8752),
        4: Task(2493212890, 8760),
        5: Task(3095545509, 8768),
        6: Task(3697910090, 8768),
        7: Task(4300157073, 8712),
        8: Task(4902505219, 8776),
        9: Task(5504858080, 8772),

        10: Task(1657534360, 33108),
        11: Task(2084572390, 34376),
        12: Task(2596629963, 35892),
        13: Task(3220580993, 37660),
        14: Task(3944152698, 39628),
        15: Task(4802552743, 41676),
        16: Task(5774504509, 45364),
        17: Task(6904427475, 45808),
        18: Task(8136762196, 48232),
        19: Task(9588652858, 52880),

        20: Task(523534614, 29428),
        21: Task(537966977, 32128),
        22: Task(552977984, 34352),
        23: Task(567015634, 38588),
        24: Task(582405367, 39152),
        25: Task(598134853, 41524),
        26: Task(615797109, 43876),
        27: Task(627291754, 48484),
        28: Task(643582695, 51024),
        29: Task(658656168, 51412),

        30: Task(7825468822, 225904),
        31: Task(8161033165, 241248),
        32: Task(8481711819, 262528),
        33: Task(8787361472, 281760),
        34: Task(9163415486, 302792),
        35: Task(9527258845, 321680),
        36: Task(9761101484, 340404),
        37: Task(10090950243, 362196),
        38: Task(10373445603, 383312),
        39: Task(10673581615, 400620),

        40: Task(19140032841, 409632),
        41: Task(19149226033, 417604),
        42: Task(19194459146, 424192),
        43: Task(19316838349, 439716),
        44: Task(19414124951, 456188),
        45: Task(19564180312, 512640),
        46: Task(19738811896, 551184),
        47: Task(19941705200, 609924),
        48: Task(20149166535, 655268),
        49: Task(20795678996, 732852),

        50: Task(3665893785, 193372),
        51: Task(3665533594, 225360),
        52: Task(3664847276, 243312),
        53: Task(3664453979, 262592),
        54: Task(3663897203, 282264),
        55: Task(3665494787, 304300),
        56: Task(3664388401, 322868),
        57: Task(3664497732, 341648),
        58: Task(3663691291, 361640),
        59: Task(3664732914, 381756),
    },

    'aarch64-rpi3': {
        0: Task(32360695, 8064),
        1: Task(459336927, 7476),
        2: Task(886365716, 7484),
        3: Task(1313349540, 7632),
        4: Task(1740341356, 7616),
        5: Task(2167353565, 7488),
        6: Task(2594351699, 7596),
        7: Task(3021371653, 7616),
        8: Task(3448385883, 7488),
        9: Task(3875357367, 7620),

        10: Task(1731404048, 33904),
        11: Task(2159100451, 35164),
        12: Task(2670564918, 36728),
        13: Task(3295246437, 38424),
        14: Task(4018758542, 40200),
        15: Task(4877545275, 41992),
        16: Task(5849612154, 44308),
        17: Task(6979506713, 46620),
        18: Task(8236205972, 48740),
        19: Task(9675312655, 51604),

        20: Task(595617025, 30296),
        21: Task(607655416, 33008),
        22: Task(619982756, 35144),
        23: Task(631970091, 37640),
        24: Task(643159555, 40096),
        25: Task(658774346, 42532),
        26: Task(674186016, 45140),
        27: Task(683682000, 47512),
        28: Task(697205531, 49684),
        29: Task(710365175, 52096),

        30: Task(6638411436, 210372),
        31: Task(6900574270, 227256),
        32: Task(7420390442, 244432),
        33: Task(7603127146, 251404),
        34: Task(8045060152, 265548),
        35: Task(8321157075, 273772),
        36: Task(8921059306, 285200),
        37: Task(11124942194, 298068),
        38: Task(9845334285, 278388),
        39: Task(10996165571, 291228),

        40: Task(19291199511, 283144),
        41: Task(19361084608, 281920),
        42: Task(19542062806, 281288),
        43: Task(19512297268, 281768),
        44: Task(19654680834, 279736),
        45: Task(20095124393, 264388),
        46: Task(20454376546, 273868),
        47: Task(21598530408, 283568),
        48: Task(21398984046, 287944),
        49: Task(25167193405, 285424),

        50: Task(3311681654, 194636),
        51: Task(3315372668, 214080),
        52: Task(3314190320, 234480),
        53: Task(3314302112, 252896),
        54: Task(3315686342, 257976),
        55: Task(3313847986, 258312),
        56: Task(3315117552, 275248),
        57: Task(3315618216, 296988),
        58: Task(3315506531, 299980),
        59: Task(3315719259, 277568),
    },

    'aarch64-rpi4': {
        0: Task(45243078, 8656),
        1: Task(441596296, 8108),
        2: Task(837967784, 8108),
        3: Task(1234366298, 8108),
        4: Task(1628385509, 8112),
        5: Task(2027196721, 8108),
        6: Task(2427197598, 8108),
        7: Task(2824207558, 8100),
        8: Task(3221162967, 8108),
        9: Task(3618206029, 8108),

        10: Task(1428841994, 36220),
        11: Task(1856299094, 37548),
        12: Task(2368507224, 39136),
        13: Task(2993218392, 40704),
        14: Task(3716930018, 42568),
        15: Task(4576020749, 44416),
        16: Task(5548430698, 46528),
        17: Task(6678976550, 48892),
        18: Task(7936299843, 51264),
        19: Task(9375774518, 53648),

        20: Task(291948686, 32728),
        21: Task(305007140, 35124),
        22: Task(317930309, 37496),
        23: Task(330803133, 39880),
        24: Task(344214098, 42412),
        25: Task(359688305, 44644),
        26: Task(371147274, 47172),
        27: Task(386335987, 49632),
        28: Task(401050906, 52016),
        29: Task(414542436, 54456),

        30: Task(7534544310, 219124),
        31: Task(7827232762, 237496),
        32: Task(8196524889, 256912),
        33: Task(8460710009, 277076),
        34: Task(8760332535, 297068),
        35: Task(9067858553, 317008),
        36: Task(9460769095, 338000),
        37: Task(9827516562, 357456),
        38: Task(10047523927, 378064),
        39: Task(10343300662, 398024),

        40: Task(19242388591, 407060),
        41: Task(19285618977, 422236),
        42: Task(19680417406, 423948),
        43: Task(19475546886, 441512),
        44: Task(19663178765, 472680),
        45: Task(19607798119, 512920),
        46: Task(19715890882, 555440),
        47: Task(19864256786, 602756),
        48: Task(20040350728, 666220),
        49: Task(20867765717, 730920),

        50: Task(6172594103, 196980),
        51: Task(6213024263, 219120),
        52: Task(6264296015, 237520),
        53: Task(6336658527, 256924),
        54: Task(6442588754, 277088),
        55: Task(6514396338, 297072),
        56: Task(6627339653, 317032),
        57: Task(6751233135, 337096),
        58: Task(6884346604, 357692),
        59: Task(7030333433, 378244),
    },

    'aarch64-tx2': {
        0: Task(70977619, 8616),
        1: Task(684599645, 8560),
        2: Task(1298263004, 8560),
        3: Task(1911907999, 8484),
        4: Task(2525646557, 8552),
        5: Task(3139272302, 8680),
        6: Task(3752918973, 8540),
        7: Task(4366568836, 8584),
        8: Task(4980311356, 8556),
        9: Task(5593911901, 8584),

        10: Task(1634040124, 35204),
        11: Task(2061258650, 36392),
        12: Task(2572884736, 38080),
        13: Task(3197493925, 39772),
        14: Task(3920494801, 41592),
        15: Task(4779188001, 43672),
        16: Task(5751269266, 47504),
        17: Task(6881208950, 47900),
        18: Task(8138308083, 52100),
        19: Task(9576783317, 52952),

        20: Task(500745429, 31480),
        21: Task(514960453, 34248),
        22: Task(529437812, 36300),
        23: Task(543748003, 38824),
        24: Task(559012979, 41284),
        25: Task(574381909, 43596),
        26: Task(592943289, 46220),
        27: Task(604403819, 48308),
        28: Task(620615607, 50892),
        29: Task(635756156, 53472),

        30: Task(7534544310, 219124),
        31: Task(7827232762, 237496),
        32: Task(8196524889, 256912),
        33: Task(8460710009, 277076),
        34: Task(8760332535, 297068),
        35: Task(9067858553, 317008),
        36: Task(9460769095, 338000),
        37: Task(9827516562, 357456),
        38: Task(10047523927, 378064),
        39: Task(10343300662, 398024),

        40: Task(19242388591, 407060),
        41: Task(19285618977, 422236),
        42: Task(19680417406, 423948),
        43: Task(19475546886, 441512),
        44: Task(19663178765, 472680),
        45: Task(19607798119, 512920),
        46: Task(19715890882, 555440),
        47: Task(19864256786, 602756),
        48: Task(20040350728, 666220),
        49: Task(20867765717, 730920),

        50: Task(6172594103, 196980),
        51: Task(6213024263, 219120),
        52: Task(6264296015, 237520),
        53: Task(6336658527, 256924),
        54: Task(6442588754, 277088),
        55: Task(6514396338, 297072),
        56: Task(6627339653, 317032),
        57: Task(6751233135, 337096),
        58: Task(6884346604, 357692),
        59: Task(7030333433, 378244),
    },

    'x86_64-pc': {
        0: Task(459325960, 7464),
        1: Task(886354884, 7376),
        2: Task(1313354711, 7496),
        3: Task(1740435521, 7380),
        4: Task(2167353560, 7376),
        5: Task(2594311971, 7488),
        6: Task(3021406406, 7460),
        7: Task(3448343252, 7484),
        8: Task(3875417462, 7484),
        9: Task(4302362416, 7500),

        10: Task(4308696059, 37304),
        11: Task(5726251592, 40112),
        12: Task(7454959898, 43776),
        13: Task(9524912292, 47212),
        14: Task(11967812230, 51400),
        15: Task(14815489823, 55792),
        16: Task(18056186224, 60536),
        17: Task(21750177333, 65280),
        18: Task(25927403084, 70712),
        19: Task(30619003800, 76336),

        20: Task(459238339, 24024),
        21: Task(461493645, 24604),
        22: Task(462138930, 24620),
        23: Task(462189053, 24484),
        24: Task(462426050, 24600),
        25: Task(460854789, 24412),
        26: Task(462730871, 24316),
        27: Task(460316118, 25056),
        28: Task(463780163, 25072),
        29: Task(460506910, 24372),

        30: Task(7725533053, 371380),
        31: Task(7983313680, 390484),
        32: Task(8250724708, 408304),
        33: Task(8510488602, 428080),
        34: Task(8772181888, 446000),
        35: Task(9036444754, 464864),
        36: Task(9293152099, 483380),
        37: Task(9561099144, 503016),
        38: Task(9820307963, 521020),
        39: Task(10084271866, 539992),

        40: Task(18682790593, 2497848),
        41: Task(18736616370, 2507028),
        42: Task(18799857676, 2521452),
        43: Task(18880281366, 2528384),
        44: Task(18975297208, 2559484),
        45: Task(19092197567, 2597780),
        46: Task(19228022484, 2641128),
        47: Task(19384822976, 2694236),
        48: Task(19551399212, 2752444),
        49: Task(20082984124, 2816328),

        50: Task(4805242011, 348552),
        51: Task(4804729076, 371380),
        52: Task(4805289890, 390616),
        53: Task(4804635545, 409296),
        54: Task(4804654330, 427288),
        55: Task(4804012421, 446292),
        56: Task(4803377172, 464444),
        57: Task(4803561298, 483148),
        58: Task(4805207233, 502368),
        59: Task(4804938273, 521196),
    }
}

# Per-task, per-executor network bandwidth measurements.
_TaskBandwidthData = {
    0: [27.39, 11.43, 13.61, 16.46, 18.1, 19.41, 17.78, 23.06, 13.34, 28.15],
    1: [25.88, 11.91, 13.71, 13.45, 22.5, 20.05, 15.94, 22.49, 14.37, 28.54],
    2: [27.38, 14.23, 12.52, 16.97, 19.43, 22.17, 18.78, 21.21, 11.85, 23.74],
    3: [26.99, 13.71, 13.17, 15.56, 20.48, 19.61, 16.53, 23.86, 14.17, 29.7],
    4: [25.9, 11.27, 12.8, 15.76, 20.3, 20.69, 27.24, 18.61, 14.06, 28.01],
    5: [25.26, 10.24, 12.16, 17.43, 17.15, 15.31, 16.05, 16.52, 15.29, 38.34],
    6: [28.67, 13.51, 13.32, 16.67, 19.29, 15.35, 19.38, 19.97, 14.71, 23.35],
    7: [25.26, 11.88, 13.98, 16.95, 17.32, 19.16, 19.86, 22.5, 14.95, 25.38],
    8: [25.72, 11.27, 13.88, 13.57, 14.34, 16.28, 19.44, 21.58, 13.94, 24.82],
    9: [26.98, 13.4, 12.89, 14.97, 18.17, 15.24, 18.29, 20.39, 13.44, 29.28],
    10: [21819.27, 26437.66, 37109.08, 43936.65, 48306.4, 47374.9, 50466.85, 48135.73, 45189.08, 56291.65],
    11: [21675.83, 27995.37, 43427.37, 46120.53, 53238.85, 51583.04, 53067.73, 51869.13, 51578.08, 59844.1],
    12: [18880.06, 31203.86, 46813.78, 44913.28, 56313.84, 55352.45, 61978.65, 59130.83, 53802.72, 69293.84],
    13: [22310.82, 30987.77, 46627.27, 53278.48, 61132.63, 59204.5, 63157.98, 59921.15, 28789.1, 69424.24],
    14: [19901.58, 37452.44, 50698.22, 56004.78, 65842.42, 59760.87, 65820.52, 65778.37, 44675.87, 71406.12],
    15: [22389.11, 37191.98, 52539.23, 54854.89, 66576.51, 64827.18, 72308.92, 68541.11, 43752.73, 73203.71],
    16: [22664.1, 35622.58, 54046.29, 56324.94, 69535.07, 66188.67, 68449.82, 68684.2, 53191.75, 75724.44],
    17: [21545.73, 0, 0, 59823.84, 71125.89, 69477.87, 68300.84, 68582.79, 66251.43, 76795.25],
    18: [21040.58, 0, 0, 63322.69, 73789.65, 68893.97, 71462.89, 71065.84, 58280.05, 74141.14],
    19: [20759.79, 0, 0, 59170.64, 73313.36, 71635.76, 74127.23, 71574.44, 46893.22, 77358.18],
    20: [14254.46, 28000.34, 40685.05, 43029.3, 51099.25, 50751.04, 51308.39, 49736.42, 19458.21, 59671.6],
    21: [17051.1, 32185.56, 38893.16, 39097.03, 40302.44, 40801.64, 39708.97, 40919.31, 32034.68, 39519.18],
    22: [17659.27, 34797.49, 48252.98, 47477.69, 50788.24, 49452.2, 50264.38, 50568.93, 40950.71, 47912.53],
    23: [19830.3, 33911.91, 52938.87, 51050.05, 57382.65, 58172.39, 58273.37, 57821.02, 48614.12, 54157.84],
    24: [20174.7, 35527.62, 60340.26, 56491.8, 65411.79, 61685.15, 64213.31, 62953.07, 54432.14, 59411.36],
    25: [21138.39, 38797.97, 66577.92, 59570.52, 67937.94, 67380.7, 67855.2, 68040.88, 59174.56, 63998.4],
    26: [20327.53, 37461.89, 55810.74, 56394.83, 73200.51, 71187.84, 71248.89, 70688.71, 63044.42, 66638.24],
    27: [20745.84, 37072.67, 56318.19, 56997.32, 76193.08, 71802.6, 75498.67, 74263.7, 64148.02, 68237.39],
    28: [22942.64, 35831.44, 51243.71, 59026.76, 75262.03, 66317.31, 74743.27, 67754.04, 66236.48, 78855.78],
    29: [20451.45, 32990.21, 51038.25, 61699.24, 75354.54, 73656.99, 76415.09, 75156.03, 69177.31, 81600.39],
    30: [15247.91, 17508.24, 26238.21, 24927.04, 29305.42, 26504.87, 27916.93, 30372.38, 23825.07, 30503.53],
    31: [20679.68, 26501.94, 0, 37129.84, 40473.78, 35645.07, 41940.76, 40313.38, 36860.53, 49369.34],
    32: [23840.07, 27502.84, 35875.41, 42390.13, 50554.43, 46191.27, 50372.34, 46163.67, 42175.41, 54410.09],
    33: [23543.73, 31879.84, 0, 50075.85, 53510.06, 52347.36, 55092.8, 54451.62, 49980.47, 60246.75],
    34: [24598.54, 32522.59, 0, 53716.92, 59662.33, 53955.14, 62855.05, 58799.12, 56786.55, 65641.48],
    35: [27554.8, 31885.22, 0, 52725.81, 58766.45, 58651.85, 62478.18, 61783.53, 59833.88, 69081.55],
    36: [26541.44, 29916.78, 0, 55927.74, 66383.63, 60889.83, 64738.31, 63322.84, 62232.72, 72900.49],
    37: [26553.71, 30065.1, 0, 60667.49, 68538.34, 65280.72, 66927.44, 65903.44, 65865.81, 73326.65],
    38: [27071.32, 30013.98, 0, 58766.48, 69115.45, 65138.33, 67859.19, 65957.82, 67594.39, 74507.86],
    39: [25609.73, 30226.03, 0, 64986.18, 69518.65, 66379.83, 72075.11, 67963.38, 69250.08, 73389.14],
    40: [4961.37, 0, 0, 4212.4, 4235.29, 3655.57, 4502.41, 4595.82, 4087.86, 3601.49],
    41: [9826.79, 0, 0, 10656.72, 12278.38, 11505.7, 12468.15, 11885.17, 10502.63, 9885.45],
    42: [15897.63, 0, 0, 19062.49, 21225.73, 19218.87, 19837.73, 20689.76, 16936.31, 19194.29],
    43: [18390.92, 0, 0, 24276.15, 27070.71, 26431.98, 27942.83, 28889.74, 23505.48, 23357.8],
    44: [20020.76, 0, 0, 30397.73, 33858.12, 33931.97, 34400.9, 33690.58, 31742.42, 30641.83],
    45: [24151.17, 0, 0, 37344.08, 41114.4, 38750.33, 40959.25, 35490.12, 38365.52, 37650.15],
    46: [23569.68, 0, 0, 40411.89, 44520.04, 42173.66, 46316.28, 44411.58, 43593.16, 42023.23],
    47: [24053.96, 0, 0, 44493.29, 48836.75, 45789.96, 51556.93, 49400.73, 47625.34, 46212.57],
    48: [25667.31, 0, 0, 45918.63, 54577.89, 49666.3, 52818.41, 53384.59, 49518.77, 48753.3],
    49: [22557.55, 0, 0, 38186.36, 46311.55, 39242.76, 44605.11, 42545.76, 38015.5, 37946.08],
    50: [2630.83, 1192.13, 809.48, 1508.1, 1961.36, 1801.44, 1605.63, 1877.69, 1462.96, 2721.33],
    51: [7049.79, 3617.63, 2859.52, 5705.81, 6700.76, 5387.47, 5574.18, 6898.14, 5170.79, 7234.64],
    52: [10639.05, 5510.93, 5473.22, 8552.91, 11460.62, 10613.99, 11052.76, 11032.12, 9274.07, 14990.82],
    53: [15205.55, 9840.9, 9160.18, 13866.11, 17329.42, 15270.29, 18686.47, 20470.08, 14101.11, 18931.85],
    54: [15250.74, 13782.17, 13017.54, 21495.36, 26640.16, 21957.34, 27059.59, 24015.22, 20499.47, 30468.26],
    55: [20604.37, 17525.84, 14846.6, 27173.46, 28417.07, 28797.89, 34196.38, 27713.42, 24802.48, 34617.18],
    56: [20564.08, 17701.58, 18044.14, 32328.43, 34397.99, 36828.27, 36545.12, 33466.42, 31559.45, 41956.52],
    57: [20312.44, 19175.52, 21005.65, 35263.37, 40364.83, 34320.21, 41301.91, 40270.3, 33245.7, 44634.66],
    58: [20156.06, 23156.54, 23852.18, 39771.61, 41390.16, 39760.85, 44464.65, 42183.65, 39337.05, 53953.37],
    59: [23656.44, 24125.01, 25053.88, 36595.89, 46037.3, 42913.51, 46406.66, 48459.08, 43452.85, 48387.81],
}

# Total worst-case data sent over the network for each task.
# Includes the response sent from the executor.
_TaskSizeData = {
    0: 415,
    1: 416,
    2: 416,
    3: 428,
    4: 417,
    5: 417,
    6: 428,
    7: 416,
    8: 416,
    9: 416,
    10: 3000414,
    11: 3710047,
    12: 4480267,
    13: 5339083,
    14: 6255823,
    15: 7263832,
    16: 8327081,
    17: 9484265,
    18: 10694045,
    19: 12000413,
    20: 3175611,
    21: 6350811,
    22: 9526011,
    23: 12701222,
    24: 15876410,
    25: 19051622,
    26: 22226811,
    27: 25402011,
    28: 28577209,
    29: 31752419,
    30: 920644,
    31: 1840868,
    32: 2761093,
    33: 3681317,
    34: 4601533,
    35: 5521756,
    36: 6441981,
    37: 7362215,
    38: 8282432,
    39: 9202644,
    40: 124002,
    41: 401071,
    42: 753010,
    43: 1156982,
    44: 1649207,
    45: 2149569,
    46: 2712448,
    47: 3301974,
    48: 3958384,
    49: 2330543,
    50: 45088,
    51: 153293,
    52: 318385,
    53: 541173,
    54: 817389,
    55: 1126728,
    56: 1460204,
    57: 1814204,
    58: 2172920,
    59: 2543514,
}
