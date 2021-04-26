from .node import Node


class Robot(Node):
    arduino_reset_pin = 2
    valves = [15, 16]
    hw_config = {
        'valves': [37, 39],
        'motors': [
            {
                'pin_pulse': 12,
                'pin_dir': 11,
                'pin_limit_n': 15,
                'pin_limit_p': 16,
                'microstep': 2500,
                'course': 100000,
                'homing_delay': 500,
                'home_retract': 500,
            },
            {
                'pin_pulse': 9,
                'pin_dir': 8,
                'pin_limit_n': 14,
                # 'pin_limit_p': 0,
                'microstep': 2500,
                'course': 50000,
                'homing_delay': 200,
                'home_retract': 100,
            },
        ]
    }


ROBOTS = [
    Robot('192.168.44.11'),
    Robot('192.168.44.12'),
]
