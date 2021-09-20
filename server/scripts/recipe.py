import asyncio


N = 5
# Basics
FEED_X = 5000  # 6500  # 8500
FEED_Y_UP = 5000  # 8000
FEED_Y_DOWN = 5000  # 9000
FEED_Z_UP = 10000  # 15000
FEED_Z_DOWN = 15000  # 25000

# Park
X_PARK = 10
Y_PARK = 40


# Capping
X_CAPPING = 51.25
Y_CAPPING_DOWN_1 = 22
Y_CAPPING_DOWN_2 = 10
FEED_Y_CAPPING = 1000
T_RAIL_FIXED_JACK = .7
T_RAIL_MOVING_JACK = .7

assert Y_CAPPING_DOWN_2 < Y_PARK

# Station
FEED_DANCE = 40000

# Vision
ALIGN_SPEED_DOSING = 25000
ALIGN_SPEED_HOLDER = 25000

# Rail
FEED_RAIL_FREE = 30000
FEED_RAIL_INTACT = 16000
D_STANDBY = 250
D_MIN = D_STANDBY - 25 * N
assert D_MIN >= 0
T_RAIL_JACK1 = 1.1
T_RAIL_JACK2 = 1.1
T_RAIL_FEEDER_JACK_PERCENTAGE = .3

# Feeder
FEED_FEEDER_DELIVER = 70000
FEEDER_Z_IDLE = 16
FEEDER_Z_DELIVER = 719


async def gather_all_nodes(system, ALL_NODES):
    stations = [node for node in ALL_NODES if node.name.startswith('Station ')]
    robots = [node for node in ALL_NODES if node.name.startswith('Robot ')]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]

    all_nodes = stations + robots + [rail, feeder]

    # All Nodes Ready?
    for node in all_nodes:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    return all_nodes, feeder, rail, robots, stations
