import asyncio
from .robot import Robot


class Rail(Robot):
    type = 'rail'
    arduino_reset_pin = 2

    g2core_config_base = [
        (1, {
            'ma': 2,  # map to Z
            'sa': 1.8,  # step angle 1.8
            'tr': 5,  # travel per rev = 5mm
            'mi': 8,  # microstep = 2
            'po': 1,  # direction
        }),
        ('z', {
            'am': 1,  # standard axis mode
            'vm': 10000,  # max speed
            'fr': 10000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 900,  # max travel
            'jm': 2500,  # max jerk
            'jh': 4000,  # hominzg jerk
            'hi': 2,  # home switch
            'hd': 0,  # homing direction
            'sv': 2000,  # home search speed
            'lv': 200,  # latch speed
            'zb': 1,  # zero backoff
        }),
        ('di2mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di2ac', 1),
        ('di2fn', 1),
        ('gpa', 2),  # equivalent of G64
        ('sv', 2),  # Status report enabled
        ('sr', {'line': True, 'posz': True, 'stat': True}),
        ('si', 250),  # also every 250ms
    ]

    hw_config_base = {
        'valves': {
            'reserve1': 1,
            'reserve2': 2,
            'reserve3': 3,
            'reserve4': 4,
            'reserve5': 5,
            'reserve6': 6,
            'reserve7': 7,
            'reserve8': 8,
            'moving': 9,
            'fixed': 10,
        },
        'di': {
            'z-': 1,
        },
        'encoders': {
            'posz': ['enc1', 320.0, 1],  # encoder key, ratio, telorance
        }

    }

    async def set_valves(self, values):
        values = [0] * 8 + values
        return await super(Rail, self).set_valves(values)

    async def home(self):
        await self.send_command_raw('!\n\x04', wait_start=[], wait_completion=False)
        await asyncio.sleep(1)

        await self.send_command_raw('G28.2 Z0')

        # reset encoder
        await self.send_command_raw('G28.5')
        await self.send_command_raw('G1 Z1 F1000')
        await self.send_command_raw('G1 Z0 F1000')
        await asyncio.sleep(1)

    async def is_homed(self, telorance=50):
        return True
