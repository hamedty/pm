from .station import STATIONS, Station
from .robot import ROBOTS, Robot
from .rail import RAILS


ALL_NODES = STATIONS + ROBOTS + RAILS
ALL_NODES = [node for node in ALL_NODES if node]
# ALL_NODES = [Robot('192.168.44.51')]
ALL_NODES = [

    Robot('192.168.44.51'),  # Robot 01
    # Station('192.168.44.52'),  # station 03
    # Station('192.168.44.55'),  # station 06
    # Station('192.168.44.53'),  # station 08
    # Station('192.168.44.50'),  # station 09
    # Station('192.168.44.54'),  # station 10 - no usb cable

]

# ALL_NODES = [Station('127.0.0.1')]
