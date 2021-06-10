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
            'mi': 2,  # microstep = 2
            'po': 1,  # direction
        }),
        ('z', {
            'am': 1,  # standard axis mode
            'vm': 9000,  # max speed
            'fr': 800000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 800,  # max travel
            'jm': 9000,  # max jerk
            'jh': 9000,  # hominzg jerk
            'hi': 1,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 200,  # latch speed
            'zb': 1,  # zero backoff
        }),
        ('di1mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di1ac', 1),
        ('di1fn', 1),
    ]

    hw_config_base = {
        'valves': {
            'fixed': 1,
            'moving': 2,
        },
        'di': {
            'x-': 1,
        },
        'encoders': {
            'z': ['enc2', 480.0, .1],  # encoder key, ratio, telorance
        }

    }

    async def goto(self, y):
        return await super(Rail, self).goto(y=y)

    async def is_homed(self, telorance=50):
        return True
