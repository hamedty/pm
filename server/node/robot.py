from .node import Node
import asyncio


class Robot(Node):
    type = 'robot'
    arduino_reset_pin = 2
    HOMMED_AXES = ['x', 'y']

    g2core_config_base = [
        # X - Holder Motor
        (1, {
            'ma': 0,  # map to X
            'sa': 1.8,  # step angle 1.8
            'tr': 20,  # travel per rev = 5mm
            'mi': 2,  # microstep = 2
            'po': 1,  # direction
        }),
        ('x', {
            'am': 1,  # standard axis mode
            'vm': 60000,  # max speed
            'fr': 60000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 400,  # max travel
            'jm': 900,  # max jerk
            'jh': 1000,  # hominzg jerk
            'hi': 1,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 200,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di1mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di1ac', 2),
        ('di1fn', 1),
        ('di2mo', 1),  # Limit Switch + - Mode = Active High - NC
        ('di2ac', 2),  # Limit Switch + - Action = Fast Stop
        ('di2fn', 1),  # Limit Switch + - Function = Limit

        # Y - Dosing Motor
        (2, {
            'ma': 1,  # map to Y
            'sa': 1.8,  # step angle 1.8
            'tr': 5,  # travel per rev = 5mm
            'mi': 4,  # microstep = 2
            'po': 1,  # direction
        }),
        ('y', {
            'am': 1,  # standard axis mode
            'vm': 20000,  # max speed
            'fr': 800000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 100,  # max travel
            'jm': 7000,  # max jerk
            'jh': 8000,  # homing jerk
            'hi': 3,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 200,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di3mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di3ac', 2),
        ('di3fn', 1),
        ('di4mo', 1),  # Limit Switch + - Mode = Active High - NC
        ('di4ac', 2),  # Limit Switch + - Action = Fast Stop
        ('di4fn', 1),  # Limit Switch + - Function = Limit
        ('jt', 1.00),
        ('gpa', 2),  # equivalent of G64
        ('sv', 2),  # Status report enabled
        ('sr', {'line': True, 'posx': True, 'posy': True, 'stat': True}),
        ('si', 250),  # also every 250ms
    ]

    hw_config_base = {
        'valves': {
            'dosing1': 1,
            'dosing2': 2,
            'dosing3': 3,
            'dosing4': 4,
            'dosing5': 5,
            'holder1': 6,
            'holder2': 7,
            'holder3': 8,
            'holder4': 9,
            'holder5': 10,
        },
        'di': {
            'x-': 1,
            'x+': 2,
            'y-': 3,
            'y-': 4,
        },
        'encoders': {
            # encoder key, ratio, telorance_soft, telorance_hard
            'posx': ['enc2', 120.0, 1.0, 5.0],
            'posy': ['enc1', 480.0, 1.0, 5.0],
        },
    }

    def __init__(self, *args, **kwargs):
        self._stations = set()
        self._stations_slot = [None] * 5
        super().__init__(*args, **kwargs)

    async def home_core(self):
        await self.send_command_raw('G28.2 X0')
        await self.send_command_raw('G28.2 Y0')

        # reset encoder
        await self.send_command_raw('G28.5')
        await self.send_command_raw('G1 X1 Y1 F1000')
        await self.send_command_raw('G1 X0 Y0 F1000')

    def add_station(self, station, index):
        self._stations.add(station)
        self._stations_slot[index] = station

    async def set_valves_grab_infeed(self):
        mask = [0] * 5
        for i in range(5):
            if self._stations_slot[i]:
                mask[5 - i - 1] = 1
        mask = mask * 2
        await self.set_valves(mask)

    async def do_robot(self, recipe, system):
        # ensure about stations
        stations_task1 = asyncio.gather(
            *[station.clearance(system) for station in self._stations])

        '''PICK UP'''
        Y_GRAB_IN_UP_1 = 75
        X_GRAB_IN = 284.5
        Y_GRAB_IN_DOWN = 0
        Y_GRAB_IN_UP_2 = 65
        T_GRAB_IN = 0.5

        await system.system_running.wait()
        await self.G1(y=Y_GRAB_IN_UP_1, feed=recipe.FEED_Y_UP, system=system)
        await self.G1(x=X_GRAB_IN, feed=recipe.FEED_X, system=system)
        await self.G1(y=Y_GRAB_IN_DOWN, feed=recipe.FEED_Y_DOWN, system=system)
        await self.set_valves_grab_infeed()
        await asyncio.sleep(T_GRAB_IN)
        await self.G1(y=Y_GRAB_IN_UP_2, feed=recipe.FEED_Y_UP, system=system)

        '''EXCHANGE'''
        X_INPUT = 373
        Y_INPUT_DOWN_RELEASE_HOLDER = 36
        Y_INPUT_DOWN_RELEASE_DOSING = 32
        Y_INPUT_UP = 55
        Y_INPUT_DOWN_PRESS_HOLDER = 6
        Y_INPUT_DOWN_PRE_PRESS_HOLDER = Y_INPUT_DOWN_PRESS_HOLDER + 10
        Y_OUTPUT = 80
        X_OUTPUT_SAFE = recipe.X_CAPPING

        Z_OUTPUT = 70
        Z_OUTPUT_SAFE = Z_OUTPUT - 20

        T_INPUT_RELEASE = 1.0
        T_HOLDER_JACK_CLOSE = 0.1
        T_PRE_PRESS = 0.05
        T_POST_PRESS = 0.1
        T_OUTPUT_GRIPP = 0.1
        T_OUTPUT_RELEASE = 0.2

        # ensure about stations
        await stations_task1
        await system.system_running.wait()
        await self.G1(x=X_INPUT, feed=recipe.FEED_X, system=system)
        await self.G1(y=Y_INPUT_DOWN_RELEASE_HOLDER, feed=recipe.FEED_Y_DOWN, system=system)
        await self.set_valves([None] * 5 + [0] * 5)
        await self.G1(y=Y_INPUT_DOWN_RELEASE_DOSING, feed=recipe.FEED_Y_DOWN, system=system)
        await self.set_valves([0] * 10)
        await asyncio.sleep(T_INPUT_RELEASE)
        await asyncio.gather(*[station.verify_dosing_sit_right(recipe, system) for station in self._stations])
        stations_task2 = asyncio.gather(
            *[station.G1(z=Z_OUTPUT, feed=recipe.FEED_Z_DOWN / 4.0, system=system) for station in self._stations])

        await self.G1(y=Y_INPUT_UP, feed=recipe.FEED_Y_UP, system=system)
        await self.set_valves([0] * 5 + [1] * 5)
        await asyncio.sleep(T_HOLDER_JACK_CLOSE)
        await self.G1(y=Y_INPUT_DOWN_PRE_PRESS_HOLDER, feed=recipe.FEED_Y_DOWN, system=system)
        await asyncio.sleep(T_PRE_PRESS)
        await self.G1(y=Y_INPUT_DOWN_PRESS_HOLDER, feed=recipe.FEED_Y_PRESS, system=system)
        await asyncio.sleep(T_POST_PRESS)
        await stations_task2
        await self.G1(y=Y_OUTPUT, feed=recipe.FEED_Y_UP, system=system)
        await self.set_valves([1] * 5 + [0] * 5)
        await asyncio.sleep(T_OUTPUT_GRIPP)
        await asyncio.gather(*[station.set_valves([0, 0, 0, 1]) for station in self._stations])

        await asyncio.sleep(T_OUTPUT_RELEASE)
        await asyncio.gather(*[station.G1(z=Z_OUTPUT_SAFE, feed=recipe.FEED_Z_UP, system=system) for station in self._stations])

        for station in self._stations:
            station.station_is_full_event.set()

        # TODO: This can be faster
        await self.G1(x=X_OUTPUT_SAFE, feed=recipe.FEED_X, system=system)
        for station in self._stations:
            station.station_is_safe_event.set()

        '''CAP'''
        await system.system_running.wait()
        await self.G1(x=recipe.X_CAPPING, feed=recipe.FEED_X, system=system)
        await self.G1(y=recipe.Y_CAPPING_DOWN_1, feed=recipe.FEED_Y_DOWN, system=system)
        await self.G1(y=recipe.Y_CAPPING_DOWN_2, feed=recipe.FEED_Y_CAPPING, system=system)
        await self.set_valves([0] * 10)
        await self.G1(x=recipe.X_PARK, feed=recipe.FEED_X, system=system)

    async def do_robot_park(self, recipe, system):
        await system.system_running.wait()
        await self.G1(y=recipe.Y_PARK, feed=recipe.FEED_Y_UP / 5.0, system=system)
