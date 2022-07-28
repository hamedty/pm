import time
from .node import Node
import os
import json
import asyncio


class Demo(Node):
    type = 'demo'
    arduino_reset_pin = 21
    HOMMED_AXES = ['z']

    g2core_config_base = [
        # X - Holder Motor
        (1, {
            'ma': 0,  # map to X
            'sa': 1.8,  # step angle 1.8
            'tr': 360,  # travel per rev = 360 degree
            'mi': 32,  # microstep = 32
            'po': 1,  # direction
        }),
        ('x', {
            'am': 1,  # standard axis mode
            'vm': 360000,  # max speed
            'fr': 360000,  # max feed rate
            'jm': 200000,  # max jerk
            'tn': 0,  # min travel
            'tm': 0,  # max travel
        }),
        # ('out', {7: 1, 8: 1, 9: 1}),  # Microstepping enabled - done in FW

        # Y - Dosing Motor
        (2, {
            'ma': 1,  # map to Y
            'sa': 1.8,  # step angle 1.8
            'tr': 360,  # travel per rev = 360 degree
            'mi': 32,  # microstep = 32
            'po': 1,  # direction
        }),
        ('y', {
            'am': 1,  # standard axis mode
            'vm': 360000,  # max speed
            'fr': 360000,  # max feed rate
            'jm': 200000,  # max jerk
            'tn': 0,  # min travel
            'tm': 0,  # max travel
        }),
        # ('out', {10: 1, 11: 1, 12: 1}),  # Microstepping enabled -  - done in FW

        ('di1mo', 1),  # Homing Switch - Mode = Active High - NC

        ('sv', 2),  # Status report enabled
        ('sr', {'uda0': True, 'posx': True, 'posy': True, 'stat': True}),
        ('si', 250),  # also every 250ms
    ]

    hw_config_base = {
        'valves': {
            'led': 1,
        },
        'di': {
            'microswitch': 1,  # jack verification
        },
        'encoders': {
        },
        'eac': [],
    }
