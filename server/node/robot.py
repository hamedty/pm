from .node import Node
import asyncio


class Robot(Node):
    type = 'robot'
    arduino_reset_pin = 2

    g2core_config_base = [
        # X - Holder Motor
        (1, {
            'ma': 0,  # map to X
            'sa': 1.8,  # step angle 1.8
            'tr': 5,  # travel per rev = 5mm
            'mi': 4,  # microstep = 2
            'po': 1,  # direction
        }),
        ('x', {
            'am': 1,  # standard axis mode
            'vm': 11000,  # max speed
            'fr': 10000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 400,  # max travel
            'jm': 1000,  # max jerk
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
            'posx': ['enc2', 480.0, 1.0],  # encoder key, ratio, telorance
            'posy': ['enc1', 480.0, 1.0],
        }

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
        '''PICK UP'''
        Y_GRAB_IN_UP_1 = 75
        X_GRAB_IN = 284.5
        Y_GRAB_IN_DOWN = 0
        Y_GRAB_IN_UP_2 = 65
        T_GRAB_IN = 0.5

        await self.G1(y=Y_GRAB_IN_UP_1, feed=recipe.FEED_Y_UP)
        await self.G1(x=X_GRAB_IN, feed=recipe.FEED_X)
        await self.G1(y=Y_GRAB_IN_DOWN, feed=recipe.FEED_Y_DOWN)
        await self.set_valves_grab_infeed()
        await asyncio.sleep(T_GRAB_IN)
        await self.G1(y=Y_GRAB_IN_UP_2, feed=recipe.FEED_Y_UP)

        '''EXCHANGE'''
        X_INPUT = 373
        Y_INPUT_DOWN_1 = 35
        Y_INPUT_UP = 55
        Y_INPUT_DOWN_3 = 6
        Y_INPUT_DOWN_2 = Y_INPUT_DOWN_3 + 10
        Y_OUTPUT = 80
        X_OUTPUT_SAFE = recipe.X_CAPPING

        FEED_Y_PRESS = 3000

        Z_OUTPUT = 70
        Z_OUTPUT_SAFE = Z_OUTPUT - 20

        T_INPUT_RELEASE = 0.5
        T_HOLDER_JACK_CLOSE = 0.5
        T_PRE_PRESS = 0.2
        T_POST_PRESS = 0.2
        T_OUTPUT_GRIPP = 0.1
        T_OUTPUT_RELEASE = 0.2

        # ensure about stations
        async def a(station):
            await station.station_is_done_event.wait()
            station.station_is_done_event.clear()
            await station.verify_no_holder_no_dosing()
        await asyncio.gather(*[a(station) for station in self._stations])

        await self.G1(x=X_INPUT, feed=recipe.FEED_X)
        await self.G1(y=Y_INPUT_DOWN_1, feed=recipe.FEED_Y_DOWN)
        await self.set_valves([0] * 10)
        await asyncio.sleep(T_INPUT_RELEASE)
        await asyncio.gather(*[station.verify_dosing_sit_right() for station in self._stations])
        t1 = asyncio.gather(
            *[station.G1(z=Z_OUTPUT, feed=recipe.FEED_Z_DOWN / 4.0) for station in self._stations])

        await self.G1(y=Y_INPUT_UP, feed=recipe.FEED_Y_UP)
        await self.set_valves([0] * 5 + [1] * 5)
        await asyncio.sleep(T_HOLDER_JACK_CLOSE)
        await self.G1(y=Y_INPUT_DOWN_2, feed=recipe.FEED_Y_DOWN)
        await asyncio.sleep(T_PRE_PRESS)
        await self.G1(y=Y_INPUT_DOWN_3, feed=FEED_Y_PRESS)
        await asyncio.sleep(T_POST_PRESS)
        await self.set_valves([0] * 10)
        await t1
        await self.G1(y=Y_OUTPUT, feed=recipe.FEED_Y_UP)
        await self.set_valves([1] * 5)
        await asyncio.sleep(T_OUTPUT_GRIPP)
        await asyncio.gather(*[station.set_valves([0, 0, 0, 1]) for station in self._stations])

        await asyncio.sleep(T_OUTPUT_RELEASE)
        await asyncio.gather(*[station.G1(z=Z_OUTPUT_SAFE, feed=recipe.FEED_Z_UP) for station in self._stations])

        for station in self._stations:
            station.station_is_full_event.set()

        await self.G1(x=X_OUTPUT_SAFE, feed=recipe.FEED_X)
        for station in self._stations:
            station.station_is_safe_event.set()

        '''CAP'''
        await self.G1(x=recipe.X_CAPPING, feed=recipe.FEED_X)
        await self.G1(y=recipe.Y_CAPPING_DOWN_1, feed=recipe.FEED_Y_DOWN)
        await self.G1(y=recipe.Y_CAPPING_DOWN_2, feed=recipe.FEED_Y_CAPPING)
        await self.set_valves([0] * 10)
        await self.G1(x=recipe.X_PARK, feed=recipe.FEED_X)
        await self.G1(y=recipe.Y_PARK, feed=recipe.FEED_Y_UP)
