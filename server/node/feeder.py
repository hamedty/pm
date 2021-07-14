from .node import Node
import asyncio


class Feeder(Node):
    type = 'feeder'
    arduino_reset_pin = 21

    g2core_config_base = [
        # # X - Rail Motor
        (3, {
            'ma': 0,  # map to X
            'sa': 1.8,  # step angle 1.8
            'tr': 5,  # travel per rev = 5mm
            'mi': 4,  # microstep = 4
            'po': 1,  # direction
        }),
        ('x', {
            'am': 1,  # standard axis mode
            'vm': 20000,  # max speed
            'fr': 800000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 719,  # max travel
            'jm': 20000,  # max jerk
            'jh': 8000,  # hominzg jerk
            'hi': 1,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 200,  # latch speed
            'zb': 1,  # zero backoff
        }),
        ('di1mo', 0),  # Homing Switch - Mode = Active Low - NO
        ('di1ac', 1),
        ('di1fn', 1),

        # Y - Cartridge Motor 1
        (2, {
            'ma': 1,  # map to Y
            'sa': 1.8,  # step angle 1.8
            'tr': 360,  # travel per rev = 5mm
            'mi': 2,  # microstep = 2
            'po': 1,  # direction
        }),
        ('y', {
            'am': 1,  # standard axis mode
            'vm': 360 * 1000,  # max speed
            'fr': 360 * 1000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 200,  # max travel
            'jm': 100000,  # max jerk
            'jh': 100000,  # hominzg jerk
            'hi': 2,  # home switch
            'hd': 0,  # homing direction
            'sv': 360 * 5,  # home search speed
            'lv': 360,  # latch speed
            'zb': 1,  # zero backoff
        }),
        ('di2mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di2ac', 1),
        ('di2fn', 1),

        # Z - Cartridge Motor 2
        ('di3mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di3ac', 1),
        ('di3fn', 1),
        (1, {
            'ma': 2,  # map to Z
            'sa': 1.8,  # step angle 1.8
            'tr': 360,  # travel per rev = 5mm
            'mi': 4,  # microstep = 2
            'po': 1,  # direction
        }),
        ('z', {
            'am': 1,  # standard axis mode
            'vm': 360 * 1000,  # max speed
            'fr': 360 * 1000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 200,  # max travel
            'jm': 90 * 1000,  # max jerk
            'jh': 90000,  # hominzg jerk
            'hi': 3,  # home switch
            'hd': 0,  # homing direction
            'sv': 5000,  # home search speed
            'lv': 5000,  # latch speed
            'zb': 1,  # zero backoff
        }),


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
            'x-': 1,
        },
        'encoders': {
            'posx': ['enc1', 480.0, 1.0],  # encoder key, ratio, telorance
        }

    }

    async def home(self):
        await self.send_command_raw('!\n\x04', wait_start=[], wait_completion=False)
        await asyncio.sleep(1)

        # rail
        await self.send_command_raw('G28.2 X0')

        # cartridge pickers
        # await self.send_command_raw('G28.2 Y0')
        await self.send_command_raw('G28.2 Z0')

        # # reset encoder
        await self.send_command_raw('G28.5')
        await self.send_command_raw('G1 X1 F1000')
        await self.send_command_raw('G1 X0 F1000')
