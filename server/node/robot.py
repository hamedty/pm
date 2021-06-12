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
            'mi': 2,  # microstep = 2
            'po': 1,  # direction
        }),
        ('x', {
            'am': 1,  # standard axis mode
            'vm': 7000,  # max speed
            'fr': 800000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 400,  # max travel
            'jm': 7000,  # max jerk
            'jh': 7000,  # hominzg jerk
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
            'mi': 2,  # microstep = 2
            'po': 1,  # direction
        }),
        ('y', {
            'am': 1,  # standard axis mode
            'vm': 6000,  # max speed
            'fr': 800000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 100,  # max travel
            'jm': 5000,  # max jerk
            'jh': 5000,  # homing jerk
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
            'posx': ['enc2', 480.0, .2],  # encoder key, ratio, telorance
            'posy': ['enc1', 480.0, .2],
        }

    }

    def __init__(self, name, ip, arduino_id):
        self.arduino_id = arduino_id
        super(Robot, self).__init__(name, ip)

    async def home(self):
        # assert limit switch bala nakhorde
        # await self.send_command_raw('G54')
        # await self.send_command_raw('G10 L20 P1 Y0')
        # await self.send_command_raw('G1 Y10 F500')

        # await self.send_command_raw('$clear')

        # await self.send_command_raw('{lim:0}')
        # await self.send_command_raw('G10 L20 P1 Y10')
        # await self.send_command_raw('G1 Y0 F500')
        # await self.send_command_raw('{lim:1}')

        # assert limit switch bala nakhorde

        # assert Limit Switch Y+ == 1
        await self.send_command({'verb': 'encoder_check_enable', 'enable': False})
        await self.send_command_raw('G28.2 X0', wait=[])
        await self.send_command_raw('G28.2 Y0')
        await self.send_command({'verb': 'encoder_check_enable', 'enable': True})

    async def send_command(self, command, **kwargs):
        command.update(arduino_index=self.arduino_id)
        return await super(Robot, self).send_command(command, **kwargs)

    async def goto(self, x=None, y=None, z=None):
        if x is not None:
            c = 'G0 X%d' % x

        if y is not None:
            c = 'G0 Y%d' % y

        if z is not None:
            c = 'G0 Z%d' % z

        # return await self.send_command({'verb': 'move_motors', 'moves': [y, x]}, assert_success=True)
        status = await self.send_command_raw(c)
        print(status)

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
