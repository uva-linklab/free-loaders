class Task:
    def __init__(self, ins, memory):
        self.ins = ins
        self.memory = memory

class ExecutorSpecification:
    def __init__(self, max_mips, device):
        self.max_mips = max_mips
        self.device = device

_ExecutorData = {
    0: ExecutorSpecification(3085.06, 'aarch64-nano'),
    1: ExecutorSpecification(1137.11, 'aarch64-rpi3'),
    2: ExecutorSpecification(1137.11, 'aarch64-rpi3'),
    3: ExecutorSpecification(2422.04, 'aarch64-rpi4'),
    4: ExecutorSpecification(2422.04, 'aarch64-rpi4'),
    5: ExecutorSpecification(2422.04, 'aarch64-rpi4'),
    6: ExecutorSpecification(2422.04, 'aarch64-rpi4'),
    7: ExecutorSpecification(2422.04, 'aarch64-rpi4'),
    8: ExecutorSpecification(4140.84, 'aarch64-tx2'),
    9: ExecutorSpecification(15274.47, 'x86_64-pc'),
}

__TaskData = {
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

# Running times for tasks (including networking) on each machine.
# Used to calculate network transfer time for each task.
__ProfilingTotalTime = {
    'aarch64-nano': [
        (416.35, 2353.61),
        (2634.29, 12217.47),
        (2484.60, 9850.85),
        (1521.56, 7913.33),
        (7307.04, 8671.28),
        (716.47, 1835.27),
    ],

    'aarch64-rpi3': [
        (605.63, 4283.46),
        (3309.31, 30257.08),
        (560.20,  5814.92),
        (1338.50, 14474.55),
        (43654, 89494),
        (2824.89, 4314.94),
    ],

    'aarch64-rpi4': [
        (306.4, 1931.6),
        (1252.40, 7972.51),
        (1187.99, 4833.20),
        (802.45, 5879.98),
        (7533.64, 9288.47),
        (940.83, 1637.64),
    ],

    'aarch64-tx2': [
        (353.61, 1703.08),
        (1203.36, 6625.46),
        (1235.00, 2839.78),
        (1390.03, 5053.32),
        (10385.06, 11316.44),
        (1499.69, 2075.76),
    ],

    'x86_64-pc': [
        (186.69, 517.77),
        (464.90, 1856.82),
        (417.84, 3724.11),
        (362.65, 1990.57),
        (3597.15, 4089.90),
        (403.27, 662.02),
    ],
}

class HerosScheduler:

    def __init__(self, executors):
        self.executors = executors
        self.total_executor = len(executors.keys())
        self.needs_before_state = True
        self.needs_feedback = False

    def schedule(self, before_state, task):
        # Filter to only those that can handle the task.
        eligible_executors = []
        for (eid, exec_spec) in _ExecutorData.items():
            # See if the executor is defined in the dictionary in controller.py.
            is_online = str(eid) in before_state.keys()
            if not is_online:
                continue

            is_eligible = executor_is_eligible(eid, before_state[str(eid)], task)
            print('{} is online? {}, is eligible? {}'.format(eid, is_online, is_eligible))
            if is_eligible:
                eligible_executors.append(eid)

        print('[heros] executors eligible for task_id={}: {}'.format(
            task.task_id, eligible_executors))

        best_h = -999999
        best_eid = 0

        print('[heros] selection scores: {}'.format(
            [(eid, '{}'.format(round(s['h'], 2)),) for (eid, s) in before_state.items()]))

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
              f'on executer_id={best_eid}, h={round(best_h, 2)}.')

        return best_eid

    # status = 0 => successful task, status != 0 => failed task
    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        pass

def executor_is_eligible(eid, state, task):
    executor_data = _ExecutorData[eid]

    task_type_id = int(task.task_id / 10) # 0 = loop, 1 = matrix mult., 2 = FFT, ...
    task_type_level = task.task_id % 10 # 0 = MM 500x500, 1 = MM 556x556, ...

    task_m_ins = __TaskData[executor_data.device][task.task_id].ins / 1000000
    est_computation_time = task_m_ins / _ExecutorData[eid].max_mips * 1000

    min_profile_time = __ProfilingTotalTime[executor_data.device][task_type_id][0]
    max_profile_time = __ProfilingTotalTime[executor_data.device][task_type_id][1]
    # There are nine "steps" between the smallest task of the type and the largest task of the type.
    # Add to the minimum profile time the number of steps needed to interpolate the task time.
    est_profile_time = min_profile_time + ((max_profile_time - min_profile_time) / 9) * task_type_level
    est_network_time = est_profile_time - est_computation_time

    # Estimated required time in milliseconds.
    est_req_time = est_computation_time + est_network_time
    # The math should not have given us a negative number, but with linear interpolation,
    # it is possible.
    if est_network_time < 0:
        print('[heros] estimated network time is negative ({}); may be incorrect interpolation?'.format(
            round(est_network_time, 2)))
        print('[heros] est. computation time = {}, est. profile time = {}'.format(
            est_computation_time, est_profile_time))
    else:
        print('[heros] net_time + comp_time = {} + {} = {}'.format(
            round(est_network_time, 2), round(est_computation_time, 2), est_req_time))

    print('[heros] est. completion time: {} ms'.format(round(est_req_time, 2)))
    cpu_good = est_req_time <= task.deadline

    # Memory usage
    free_ram_kb = state['free-ram'] / 1024
    memory_good = free_ram_kb > __TaskData[executor_data.device][task.task_id].memory

    return cpu_good and memory_good
