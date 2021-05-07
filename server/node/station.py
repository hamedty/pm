from .node import Node


class Station(Node):
    type = 'station'
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


STATIONS = [
    # First Five
    Station('Station 1', '192.168.44.101'),
    Station('Station 2', '192.168.44.102'),
    Station('Station 3', '192.168.44.103'),
    Station('Station 4', '192.168.44.104'),
    Station('Station 5', '192.168.44.105'),

    # Second Five
    Station('Station 6', '192.168.44.106'),
    Station('Station 7', '192.168.44.107'),
    Station('Station 8', '192.168.44.108'),
    Station('Station 9', '192.168.44.109'),
    Station('Station 10', '192.168.44.110'),
]
