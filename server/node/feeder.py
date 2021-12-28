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
            'fr': 100000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 719,  # max travel
            'jm': 2500,  # max jerk
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

        ('di5mo', 0),  # Holder Input - Mode = Active Low - NC
        ('di5ac', 0),
        ('di5fn', 0),

        ('jt', 1.00),
        ('gpa', 2),  # equivalent of G64
        ('sv', 2),  # Status report enabled
        ('sr', {'uda0': True, 'posx': True,
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

    async def set_motors_working_condition(self, recipe, fast=False):
        if recipe.SERVICE_FUNC_NO_FEEDER:
            return
        if fast:
            method = self.set_motors_fast
        else:
            method = self.set_motors

        await method(
            (2, 4), (3, 4),  # Holder Downstream
            # Holder Upstream - Lift and long conveyor
            (4, 4), (7, 11),
            (1, 3750), (10, 35000),  # holder gate on/off
            (6, 25),  (8, 8)  # Cartridge Conveyor + Randomizer
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
        fast_args = [(i, int(j * 2.5)) for i, j in args]
        await self.set_motors_fast(*args)
        await asyncio.sleep(1)
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

    async def feeding_loop(self, recipe):
        await self.feeder_initial_start_event.wait()

        # if self.is_at_loc(z=recipe.FEEDER_Z_DELIVER):
        #     self.feeder_is_full_event.set()
        #     await self.feeder_is_empty_event.wait()
        #     self.feeder_is_empty_event.clear()

        await self.set_motors_working_condition(recipe)

        while not self.system_stop_event.is_set():
            t0 = time.time()

            ''' Turn on Motors '''
            await self.set_motors_working_condition(recipe, fast=True)

            ''' Fill '''
            if not recipe.SERVICE_FUNC_NO_FEEDER:
                await self.set_valves([None, 0])
                await self.G1(z=recipe.FEEDER_Z_IDLE, feed=recipe.FEED_FEEDER_COMEBACK)

                holder_mask = [1] * recipe.N
                dosing_mask = [
                    int(not recipe.SERVICE_FUNC_NO_DOSING)] * recipe.N

                command = {
                    'verb': 'feeder_process',
                    'holder_mask': holder_mask,
                    'dosing_mask': dosing_mask,
                    'cartridge_feed': not recipe.SERVICE_FUNC_NO_CARTRIDGE,
                    'z_offset': recipe.FEEDER_Z_IDLE,
                    'feed_feed': recipe.FEED_FEEDER_FEED,
                    'jerk_feed': recipe.JERK_FEEDER_FEED,
                    'jerk_idle': recipe.JERK_FEEDER_DELIVER,
                }
                await self.system.system_running.wait()
                await self.send_command(command)
                self.feeder_finished_command_event.set()

            ''' Deliver '''
            await self.feeder_rail_is_parked_event.wait()
            self.feeder_rail_is_parked_event.clear()
            await self.system.system_running.wait()
            await self.G1(z=recipe.FEEDER_Z_DELIVER, feed=recipe.FEED_FEEDER_DELIVER)

            await self.set_motors((6, 100))

            self.feeder_is_full_event.set()
            await self.feeder_is_empty_event.wait()
            self.feeder_is_empty_event.clear()
