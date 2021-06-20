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
            'zb': 1,  # zero backoff
        }),
        ('di1mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di1ac', 1),
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
            'zb': 1,  # zero backoff
        }),
        ('di3mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di3ac', 1),
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

    async def home(self):
        await self.send_command_raw('!\n\x04', wait_start=[], wait_completion=False)
        await asyncio.sleep(1)

        await self.send_command_raw('G28.2 X0')
        await self.send_command_raw('G28.2 Y0')

    async def goto(self, x=None, y=None, z=None, feed=None):
        if x is not None:
            c = 'G1 X%d' % x

        if y is not None:
            c = 'G1 Y%d' % y

        if z is not None:
            c = 'G1 Z%d' % z

        if feed is not None:
            c += ' F%d' % feed

        # return await self.send_command({'verb': 'move_motors', 'moves': [y, x]}, assert_success=True)
        status = await self.send_command_raw(c)

        command = {'sr.posx': x, 'sr.posy': y, 'sr.posz': z}
        for key, value in command.items():
            if value is None:
                continue
            enc, ratio, telorance = self.hw_config['encoders'][key.split(
                '.')[-1]]
            enc_value = status[enc] / ratio
            g2core_value = status[key]
            diversion = abs(enc_value - g2core_value)
            assert diversion < telorance, (enc_value, g2core_value)

        return

    async def move_all_the_way_up(self):
        d = self.hw_config['motors'][0]['course'] * 1.1
        command = {
            'verb': 'move_motors',
            'moves': [{'steps': d, 'delay': 300, 'blocking': 1}]
        }
        await self.send_command(command, assert_success=True)
        await asyncio.sleep(.2)
        assert self.get_status()['data']['di1']
