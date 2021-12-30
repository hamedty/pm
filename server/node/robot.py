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
            'tr': 20,  # travel per rev = 20mm
            'mi': 2,  # microstep = 2
            'po': 1,  # direction
        }),
        ('x', {
            'am': 1,  # standard axis mode
            'vm': 60000,  # max speed
            'fr': 60000,  # max feed rate
            'jm': 900,  # max jerk
            'jh': 1000,  # hominzg jerk
            'tn': 0,  # min travel
            'tm': 400,  # max travel
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
            'tr': 20,  # travel per rev = 20mm
            'mi': 4,  # microstep = 2
            'po': 1,  # direction
        }),
        ('y', {
            'am': 1,  # standard axis mode
            'vm': 20000,  # max speed
            'fr': 800000,  # max feed rate
            'jm': 7000,  # max jerk
            'jh': 8000,  # homing jerk
            'tn': 0,  # min travel
            'tm': 100,  # max travel
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
        ('sr', {'uda0': True, 'posx': True, 'posy': True, 'stat': True}),
        ('si', 250),  # also every 250ms

        ('jt', 1.2),
        ('ct', 2),
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
            'posy': ['enc1', 120.0, 1.0, 5.0],
        },
        'eac': [600, 600],
        'Y_GRAB_IN_UP_2': 64,
        'X_CAPPING': 60,
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

    async def do_robot(self, recipe):
        # ensure about stations
        stations_task1 = asyncio.gather(
            *[station.clearance() for station in self._stations])

        '''PICK UP'''
        Y_GRAB_IN_UP_1 = 75
        X_GRAB_IN = 284.5
        Y_GRAB_IN_DOWN = 0
        Y_GRAB_IN_UP_2 = self.hw_config['Y_GRAB_IN_UP_2']
        T_GRAB_IN = 0.5

        await self.system.system_running.wait()

        await self.send_command_raw(f'''
            G1 Y{Y_GRAB_IN_UP_1} F{recipe.FEED_Y_UP}
            G1 X{X_GRAB_IN} F{recipe.FEED_X}
            G1 Y{Y_GRAB_IN_DOWN} F{recipe.FEED_Y_DOWN}
        ''')

        await self.set_valves_grab_infeed()

        await self.send_command_raw(f'''
            G4 P{T_GRAB_IN:.2f}
            G1 Y{Y_GRAB_IN_UP_2} F{recipe.FEED_Y_UP}
        ''')

        '''EXCHANGE'''
        X_CAPPING = self.hw_config['X_CAPPING']

        X_INPUT = 373
        Y_INPUT_DOWN_RELEASE_HOLDER = 36
        Y_INPUT_DOWN_RELEASE_DOSING = 32
        Y_INPUT_UP = 55 + 10
        Y_INPUT_DOWN_PRESS_HOLDER = 6
        Y_INPUT_DOWN_PRE_PRESS_HOLDER = Y_INPUT_DOWN_PRESS_HOLDER + 10
        Y_OUTPUT = 80

        Z_OUTPUT = 70
        Z_OUTPUT_SAFE = Z_OUTPUT - 30

        T_INPUT_RELEASE = 1.0
        T_HOLDER_JACK_CLOSE = 0.1
        T_PRE_PRESS = 0.05
        T_POST_PRESS = 0.1
        T_OUTPUT_GRIPP = 0.2
        T_OUTPUT_RELEASE = 0.4

        # ensure about stations
        await stations_task1
        await self.system.system_running.wait()

        await self.send_command_raw(f'''
            G1 X{X_INPUT} F{recipe.FEED_X}
            G1 Y{Y_INPUT_DOWN_RELEASE_HOLDER} F{recipe.FEED_Y_DOWN_PRESS}
            M100 ({{out: {{6:0,7:0,8:0,9:0,10:0}}}})
            G1 Y{Y_INPUT_DOWN_RELEASE_DOSING} F{recipe.FEED_Y_DOWN_PRESS}
            M100 ({{out: {{1:0,2:0,3:0,4:0,5:0}}}})
        ''')

        await asyncio.sleep(T_INPUT_RELEASE)
        await asyncio.gather(*[station.verify_dosing_sit_right(recipe) for station in self._stations])

        stations_task2 = asyncio.gather(
            *[station.G1(z=Z_OUTPUT, feed=recipe.FEED_Z_DOWN / 4.0) for station in self._stations])

        await self.send_command_raw(f'''
            G1 Y{Y_INPUT_UP} F{recipe.FEED_Y_UP}
            M100 ({{out: {{1:0,2:0,3:0,4:0,5:0}}}})
            M100 ({{out: {{6:1,7:1,8:1,9:1,10:1}}}})
            G4 P{T_HOLDER_JACK_CLOSE:.2f}
            G1 Y{Y_INPUT_DOWN_PRE_PRESS_HOLDER} F{recipe.FEED_Y_DOWN}
            G4 P{T_PRE_PRESS:.2f}
            G1 Y{Y_INPUT_DOWN_PRESS_HOLDER} F{recipe.FEED_Y_DOWN_PRESS}
            G4 P{T_POST_PRESS:.2f}
        ''')

        await stations_task2

        await self.send_command_raw(f'''
            G1 Y{Y_OUTPUT} F{recipe.FEED_Y_UP}
            M100 ({{out: {{1:1,2:1,3:1,4:1,5:1}}}})
            M100 ({{out: {{6:0,7:0,8:0,9:0,10:0}}}})
        ''')

        await asyncio.sleep(T_OUTPUT_GRIPP)

        await asyncio.gather(*[station.set_valves([0, 0, 0, 1]) for station in self._stations])
        await asyncio.sleep(T_OUTPUT_RELEASE)
        await asyncio.gather(*[station.G1(z=Z_OUTPUT_SAFE, feed=recipe.FEED_Z_UP) for station in self._stations])
        for station in self._stations:
            station.station_is_full_event.set()

        ''' Move out / CAP'''
        STATION_SAFE_LIMIT = 310

        t1 = asyncio.create_task(self.send_command_raw(f'''
            G1 X{X_CAPPING} F{recipe.FEED_X}
        '''))

        while self.get_enc_loc('x') > STATION_SAFE_LIMIT:
            await asyncio.sleep(0.002)

        for station in self._stations:
            station.station_is_safe_event.set()

        await self.send_command_raw(f'''
            G1 Y{recipe.Y_CAPPING_DOWN} F{recipe.FEED_Y_DOWN_CAP}
            M100 ({{out: {{1:0,2:0,3:0,4:0,5:0}}}})
            G1 X{recipe.X_PARK} F{recipe.FEED_X}
        ''')

    async def do_robot_park(self, recipe):
        await self.system.system_running.wait()

        await self.send_command_raw(f'''
            G1 Y{recipe.Y_PARK} F{recipe.FEED_Y_UP/10}
        ''')
