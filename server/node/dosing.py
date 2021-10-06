from .node import Node
import asyncio


class Dosing(Node):
    type = 'dosing'
    arduino_reset_pin = 21

    g2core_config_base = [
        # ('di5mo', 0),  # Holder Input - Mode = Active Low - NC
        # ('di5ac', 0),
        # ('di5fn', 0),

        ('sv', 2),  # Status report enabled
        ('sr', {'line': True, 'stat': True}),
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
        },

    }

    async def home_core(self):
        pass
