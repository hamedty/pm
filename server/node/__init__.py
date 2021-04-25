from .station import STATIONS
from .robot import ROBOTS, Robot
from .rail import RAILS


ALL_NODES = STATIONS + ROBOTS + RAILS
ALL_NODES = [node for node in ALL_NODES if node]
ALL_NODES = [Robot('192.168.44.51')]
# ALL_NODES = [Station('127.0.0.1')]
