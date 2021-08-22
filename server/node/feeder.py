from .node import Node
import asyncio


class Feeder(Node):
    type = 'feeder'
    arduino_reset_pin = 21

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
            'tn': 0,  # min travel
            'tm': 100,  # max travel
            'jm': 50000,  # max jerk
            'jh': 50000,  # hominzg jerk
            'hi': 1,  # home switch
            'hd': 0,  # homing direction
            'sv': 3000,  # home search speed
            'lv': 500,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 0,  # zero backoff
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
            'zb': 0,  # zero backoff
        }),
        ('di2mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di2ac', 0),
        ('di2fn', 4),  # limit mode

        # Z - Rail Motor
        (3, {
            'ma': 2,  # map to Z
            'sa': 1.8,  # step angle 1.8
            'tr': 5,  # travel per rev = 5mm
            'mi': 4,  # microstep = 4
            'po': 1,  # direction
        }),
        ('z', {
            'am': 1,  # standard axis mode
            'vm': 20000,  # max speed
            'fr': 20000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 719,  # max travel
            'jm': 20000,  # max jerk
            'jh': 8000,  # hominzg jerk
            'hi': 3,  # home switch
            # 'sn': 3,  # minimum switch mode = limit-and-homing
            'hd': 0,  # homing direction
            'sv': 2000,  # home search speed
            'lv': 200,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di3mo', 0),  # Homing Switch - Mode = Active Low - NO
        ('di3ac', 1),
        ('di3fn', 1),


        ('jt', 1.00),
        ('gpa', 2),  # equivalent of G64
        ('sv', 2),  # Status report enabled
        ('sr', {'line': True, 'posx': True,
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
            'posz': ['enc1', 480.0, 1.0],  # encoder key, ratio, telorance
        }

    }

    async def home(self):
        await self.send_command_raw('!\n\x04', wait_start=[], wait_completion=False)
        await asyncio.sleep(1)
        #
        # cartridge pickers
        # await self.send_command_raw('G28.2 X0')
        await self.send_command_raw('G28.2 Y0')

        # # rail
        await self.send_command_raw('G28.2 Z0')

        # # # reset encoder
        await self.send_command_raw('G28.5')
        await self.send_command_raw('G1 Z16 F5000')

        self.homed = True

    async def set_motors(self, *args):
        # args = (1,30), (2,15) , ....
        if not args:  # set all zero
            args = list(zip(range(1, 10), [0] * 9))
        command = ','.join(['m%d:%d' % (i, j) for i, j in args])
        command = '{%s}' % command
        await self.send_command_raw(command)
