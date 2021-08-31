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
            'vm': 20000,  # max speed
            'fr': 800000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 400,  # max travel
            'jm': 6000,  # max jerk
            'jh': 8000,  # hominzg jerk
            'hi': 1,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 200,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di1mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di1ac', 0),
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
        ('di3ac', 0),
        ('di3fn', 1),
        ('di4mo', 1),  # Limit Switch + - Mode = Active High - NC
        ('di4ac', 1),  # Limit Switch + - Action = Fast Stop
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
