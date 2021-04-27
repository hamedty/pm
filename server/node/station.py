from .node import Node


class Station(Node):
    arduino_reset_pin = 21
    hw_config = {
        'valves': [8, 7, 6, 5, 4, 3],
        'motors': [
            {
                'pin_pulse': 43,
                'pin_dir': 42,
                'pin_microstep_0': 46,
                'pin_microstep_1': 45,
                'pin_microstep_2': 44,
                'microstep': 32,
            },
            {
                'pin_pulse': 25,
                'pin_dir': 23,
                'pin_microstep_0': 31,
                'pin_microstep_1': 29,
                'pin_microstep_2': 27,
                'microstep': 32,
            },
            {
                'pin_pulse': 48,
                'pin_dir': 47,
                'pin_microstep_0': 51,
                'pin_microstep_1': 50,
                'pin_microstep_2': 49,
                'microstep': 32,
            },
            {
                'pin_pulse': 35,
                'pin_dir': 33,
                'pin_limit_n': 28,
                'course': 12000,
                'homing_delay': 200,
                'home_retract': 100,
                'microstep': 2500,
            },
        ]
    }
    pass


STATIONS = [
    # First Five
    Station('192.168.44.101'),
    Station('192.168.44.102'),
    Station('192.168.44.103'),
    Station('192.168.44.104'),
    Station('192.168.44.105'),

    # Second Five
    Station('192.168.44.106'),
    Station('192.168.44.107'),
    Station('192.168.44.108'),
    Station('192.168.44.109'),
    Station('192.168.44.110'),
]
