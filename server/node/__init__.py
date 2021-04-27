from .station import STATIONS, Station
from .robot import ROBOTS, Robot
from .rail import RAILS


ALL_NODES = STATIONS + ROBOTS + RAILS
ALL_NODES = [node for node in ALL_NODES if node]
# ALL_NODES = [Robot('192.168.44.51')]
ALL_NODES = [

    # Robot('192.168.44.100'),  # Robot 01
    # Station('192.168.44.103'),  # station 03
    Station('192.168.44.106'),  # station 06
    Station('192.168.44.108'),  # station 08
    Station('192.168.44.109'),  # station 09
    Station('192.168.44.110'),  # station 10

]

# ALL_NODES = [Station('127.0.0.1')]
