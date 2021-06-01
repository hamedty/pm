from .station import STATIONS, Station
from .robot import ROBOTS, Robot
from .rail import RAILS, Rail


ALL_NODES = STATIONS + ROBOTS + RAILS
ALL_NODES = [node for node in ALL_NODES if node]
ALL_NODES = [
    Robot('Robot 1', '192.168.44.100', 0),
    Robot('Robot 2', '192.168.44.100', 1),
    Rail('Rail', '192.168.44.100', 2),

    Station('Station 1', '192.168.44.101'),
    Station('Station 2', '192.168.44.102'),
    Station('Station 3', '192.168.44.103'),
    Station('Station 4', '192.168.44.104'),
    Station('Station 5', '192.168.44.105'),
    Station('Station 6', '192.168.44.106'),
    Station('Station 7', '192.168.44.107'),
    Station('Station 8', '192.168.44.108'),
    Station('Station 9', '192.168.44.109'),
    Station('Station 10', '192.168.44.110'),

]
ALL_NODES_DICT = {n.name: n for n in ALL_NODES}

assert len(ALL_NODES_DICT) == len(ALL_NODES)
