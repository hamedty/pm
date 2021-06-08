from .station import Station
from .robot import Robot
from .rail import Rail


ALL_NODES = [
    # Robot('Robot 1', '192.168.44.100', 0),
    # Robot('Robot 2', '192.168.44.100', 1),
    # Rail('Rail', '192.168.44.100', 2),

    Station('Station 1', '192.168.44.101'),
    # Station('Station 2', '192.168.44.102'),
    # Station('Station 3', '192.168.44.103'),
    # Station('Station 4', '192.168.44.104'),
    # Station('Station 5', '192.168.44.105'),
    # Station('Station 6', '192.168.44.106'),
    # Station('Station 7', '192.168.44.107'),
    # Station('Station 8', '192.168.44.108'),
    # Station('Station 9', '192.168.44.109'),
    # Station('Station 10', '192.168.44.110'),

]
ALL_NODES_DICT = {n.name: n for n in ALL_NODES}

assert len(ALL_NODES_DICT) == len(ALL_NODES)

# ALL_NODES_DICT['Station 1'].set_home_retract(3, 300 + 90 + 300)
# ALL_NODES_DICT['Station 1'].hw_config['di'][1] = 26
# ALL_NODES_DICT['Station 1'].hw_config['points']['H_PUSH'] = 22500
#
# ALL_NODES_DICT['Station 2'].set_home_retract(3, 300 + 0)
# ALL_NODES_DICT['Station 2'].hw_config['points']['H_PUSH'] = 22650
#
# ALL_NODES_DICT['Station 3'].set_home_retract(3, 300 + 324)
# ALL_NODES_DICT['Station 3'].hw_config['points']['H_PUSH'] = 22770
#
# ALL_NODES_DICT['Station 4'].set_home_retract(3, 300 + 84)
# ALL_NODES_DICT['Station 4'].hw_config['points']['H_PUSH'] = 22760
#
# ALL_NODES_DICT['Station 5'].set_home_retract(3, 300 + 390)
# ALL_NODES_DICT['Station 5'].hw_config['points']['H_PUSH'] = 22710


# ALL_NODES_DICT['Station 6'].set_home_retract(3, 300)
# ALL_NODES_DICT['Station 7'].set_home_retract(3, 300)
# ALL_NODES_DICT['Station 8'].set_home_retract(3, 300)
# ALL_NODES_DICT['Station 9'].set_home_retract(3, 300)
# ALL_NODES_DICT['Station 10'].set_home_retract(3, 300)
