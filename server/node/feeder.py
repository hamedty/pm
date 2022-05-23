from .node import Node
import asyncio
import time


class Feeder(Node):
    HOMMING_RETRIES = 4
    HOMMED_AXES = ['y', 'z']

    type = 'feeder'
    arduino_reset_pin = 21
    mask = None

    g2core_config_base = [
        # X - Cartridge Motor 1
        (1, {
            'ma': 0,  # map to X
            'sa': 1.8,  # step angle 1.8
            'tr': 200,  # travel per rev - for simplicity
            'mi': 16,  # microstep = 16
            'po': 1,  # direction
        }),
        ('x', {
            'am': 1,  # standard axis mode
            'vm': 200 * 1000,  # max speed
            'fr': 200 * 1000,  # max feed rate
            'tn': -1,  # min travel
            'tm': 99,  # max travel
            'jm': 50000,  # max jerk
            'jh': 50000,  # hominzg jerk
            'hi': 1,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 500,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di1mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di1ac', 0),
        ('di1fn', 1),  # limit mode

        # Y - Cartridge Motor 2
        (2, {
            'ma': 1,  # map to Y
            'sa': 1.8,  # step angle 1.8
            'tr': 200,  # travel per rev - for simplicity
            'mi': 16,  # microstep = 16
            'po': 1,  # direction
        }),
        ('y', {
            'am': 1,  # standard axis mode
            'vm': 200 * 1000,  # max speed
            'fr': 200 * 1000,  # max feed rate
            'tn': -1,  # min travel
            'tm': 99,  # max travel
            'jm': 50000,  # max jerk
            'jh': 50000,  # hominzg jerk
            'hi': 2,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 500,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di2mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di2ac', 0),
        ('di2fn', 4),  # limit mode

        # Z - Rail Motor
        (3, {
            'ma': 2,  # map to Z
            'sa': 1.8,  # step angle 1.8
            'tr': 20,  # travel per rev = 20mm
            'mi': 2,  # microstep = 2
            'po': 1,  # direction
        }),
        ('z', {
            'am': 1,  # standard axis mode
            'vm': 100000,  # max speed
            'fr': 40000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 719,  # max travel
            'jm': 10000,  # max jerk
            'jh': 5000,  # hominzg jerk
            'hi': 3,  # home switch
            # 'sn': 3,  # minimum switch mode = limit-and-homing
            'hd': 0,  # homing direction
            'sv': 1500,  # home search speed
            'lv': 200,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di3mo', 0),  # Homing Switch - Mode = Active Low - NO
        ('di3ac', 1),
        ('di3fn', 1),

        ('di4mo', 0),  # Holder Low Level - Mode = Active Low
        ('di4ac', 0),
        ('di4fn', 0),

        ('di5mo', 0),  # Holder Input - Mode = Active Low - NC
        ('di5ac', 0),
        ('di5fn', 0),

        ('di7mo', 0),  # Holder Input - Mode = Active Low - NC
        ('di7ac', 0),
        ('di7fn', 0),

        ('di9mo', 0),  # Holder Input - Mode = Active Low - NC
        ('di9ac', 0),
        ('di9fn', 0),

        ('jt', 1.00),
        ('gpa', 2),  # equivalent of G64
        ('sv', 2),  # Status report enabled
        ('sr', {'uda0': True, 'uda1': True, 'posx': True,
                'posy': True, 'posz': True, 'stat': True}),
        ('si', 250),  # also every 250ms
    ]

    hw_config_base = {
        'valves': {
            'rail dosing': 1,
            'rail holder': 2,
            'gate': 3,
            'sub-gate 2': 4,
            'sub-gate 1': 5,
            'pusher': 6,
            'finger 1': 7,
            'finger 2': 8,
            'lift 2': 9,
            'lift 1': 10,
            'reserve 1': 11,
            'reserve 2': 12,
            'vacuum 1': 13,
            'vacuum 2': 14,
        },
        'di': {
            'z-': 1,
        },
        'encoders': {
            # encoder key, ratio, telorance_soft, telorance_hard
            'posz': ['enc1', 120.0, 1.0, 1000.0],
        },
        'eac': [600],
    }

    async def home_core(self):
        # rail
        await self.send_command_raw('G28.2 Z0')
        await self.send_command_raw('G28.5')  # reset encoder
        await asyncio.sleep(.5)  # unknown! needed to avoid g2core panic
        await self.send_command_raw('G1 Z16 F5000')  # idle position

        # cartridge pickers
        await self.send_command_raw('G28.2 Y0')
        await self.send_command_raw('G1 Y10 F60000\nG38.3 Y-100 F1000\nG10 L20 P1 Y0')
        # await self.send_command_raw('G1 Y10 F60000')
        await asyncio.sleep(.5)  # unknown! needed to avoid g2core panic

        await self.set_motors(
            (6, 300),  # Cartridge Conveyor
            (8, 20),  # Cartridge Conveyor
        )

    async def set_motors_working_condition(self, fast=False):
        if self.recipe.SERVICE_FUNC_NO_FEEDER:
            return
        if fast:
            method = self.set_motors_fast
        else:
            method = self.set_motors

        await method(
            (2, 4), (3, 4),  # Holder Downstream
            # Holder Upstream - Long conveyor and Lift
            (4, 4), (7, 11),
            (1, 3500), (10, 22000),  # holder gate on/off
            (6, 15),  (8, 8)  # Cartridge Conveyor + Randomizer
        )
        # turn on air tunnel
        await self.set_valves([None] * 9 + [1])

    async def set_motors(self, *args):
        if not args:  # set all zero
            args = list(zip(range(1, 10), [0] * 9))

        slow_motors = {7, 5, 9}  # 7 - holder elevator, 5,9 dosing
        args_fast = [(i, j)
                     for i, j in args if (i not in slow_motors) or (j == 0)]
        args_slow = [(i, j)
                     for i, j in args if (i in slow_motors) and (j != 0)]

        await self.set_motors_fast(*args_fast)
        await self.set_motors_slow(*args_slow)

    async def set_motors_fast(self, *args):
        if len(args) == 0:
            return
        command = ','.join(
            ['m%d:%d' % (i, j) for i, j in args])
        command = '{%s}' % command
        await self.send_command_raw(command, wait_start=[])

    async def set_motors_slow(self, *args):
        if len(args) == 0:
            return
        fast_args = [(i, int(j * 3)) for i, j in args]
        await self.set_motors_fast(*args)
        await asyncio.sleep(3)
        fast_args = [(i, j) for i, j in args]
        await self.set_motors_fast(*args)

    def init_events(self):
        self.feeder_is_full_event = asyncio.Event()  # setter: feeder - waiter: rail
        self.feeder_is_full_event.clear()
        self.events['feeder_is_full_event'] = self.feeder_is_full_event

        self.feeder_is_empty_event = asyncio.Event()  # setter: rail - waiter: feeder
        self.feeder_is_empty_event.clear()
        self.events['feeder_is_empty_event'] = self.feeder_is_empty_event

        self.feeder_rail_is_parked_event = asyncio.Event()  # setter: rail - waiter: feeder
        self.feeder_rail_is_parked_event.clear()
        self.events['feeder_rail_is_parked_event'] = self.feeder_rail_is_parked_event

        # setter: feeder - waiter: initial feed
        self.feeder_finished_command_event = asyncio.Event()
        self.feeder_finished_command_event.clear()
        self.events['feeder_finished_command_event'] = self.feeder_finished_command_event

        # setter: main - waiter: feeder
        self.feeder_initial_start_event = asyncio.Event()
        self.feeder_initial_start_event.clear()
        self.events['feeder_initial_start_event'] = self.feeder_initial_start_event

        self.system_stop_event = asyncio.Event()  # setter: main loop - waiter: self
        self.system_stop_event.clear()

    async def feeder_process(self, mask_holder, mask_dosing):
        disabled_stations = [8]
        # disabled_stations = []
        for s in disabled_stations:
            mask_holder[(s + 2) % 10] = 0  # station 2 -> 4
            mask_dosing[(s + 6) % 10] = 0  # station 2 -> 8

        command = {
            'verb': 'feeder_process',
            'mask_holder': mask_holder,
            'mask_dosing': mask_dosing,
            'cartridge_feed': not self.recipe.SERVICE_FUNC_NO_CARTRIDGE,
            'z_offset': self.recipe.FEEDER_Z_IDLE,
            'feed_comeback': self.recipe.FEED_FEEDER_COMEBACK,
            'feed_feed': self.recipe.FEED_FEEDER_FEED,
            'jerk_feed': self.recipe.JERK_FEEDER_FEED,
            'jerk_idle': self.recipe.JERK_FEEDER_DELIVER,
        }
        await self.send_command(command)

    async def feeding_loop(self):
        await self.feeder_initial_start_event.wait()
        await self.set_motors_working_condition()

        while not self.system_stop_event.is_set():
            t0 = time.time()

            ''' 0- update recipe '''
            updates = self.update_recipe()
            if updates:
                await self.set_motors_working_condition()

            ''' 1- Fill '''
            if not self.recipe.SERVICE_FUNC_NO_FEEDER:

                mask_holder = [1] * self.recipe.N
                mask_dosing = [1] * self.recipe.N

                await self.system.system_running.wait()
                await self.feeder_process(mask_holder, mask_dosing)
                self.feeder_finished_command_event.set()

            t1 = time.time()
            dt = t1 - t0
            print(f'Feeder Fill Loop: {dt:.1f}')
            self.system.mongo.write('timing', {'feeder_fill_loop': dt})

            ''' 2- Deliver '''
            await self.feeder_rail_is_parked_event.wait()
            self.feeder_rail_is_parked_event.clear()
            await self.system.system_running.wait()
            await self.G1(z=self.recipe.FEEDER_Z_DELIVER, feed=self.recipe.FEED_FEEDER_DELIVER)

            self.feeder_is_full_event.set()

            # home Y
            await self.send_command_raw('G38.3 Y-100 F1000\nG10 L20 P1 Y0')

            # check there are enough cartridge
            cartridge_conveyor_sensor = await self.read_metric('in9')
            if cartridge_conveyor_sensor == 0:
                error_clear_event, _ = await self.system.register_error({'message': 'کارتریج تمام شده', 'location_name': self.name, 'type': 'error'})
                await error_clear_event.wait()

            await self.feeder_is_empty_event.wait()
            self.feeder_is_empty_event.clear()
