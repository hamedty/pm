import time
import asyncio

D_STANDBY = 250
X_PARK = 0
Y_PARK = 0

# Place In
X_PLACE_IN = 373
Y_PLACE_IN = 20
Y_PLACE_IN_PRESS = 5
Y_PLACE_IN_COMEOUT = Y_PLACE_IN
T_PLACE_IN_FALL = 0.5
T_PLACE_IN_JACK_CLOSE = 0.5
T_PLACE_IN_PRESS = 0.2

# Start Station Process
X_MOVE_SAFE_STATION = 287.5
# Y_MOVE_SAFE_STATION = Y_GRAB_IN_UP_1
T_DOSING_PUSH = 0.5
T_DOSING_DANCE_UP_PRE = 0.3
T_PRESS_PRE = 0.3
T_PRESS = 1
T_PRESS_POST = 0.3
T_DOSING_DANCE_DOWN_PRE = 0.3
T_DOSING_DANCE_DOWN_POST = 0.3

# Deliver
X_DELIVER = X_PLACE_IN
Y_DELIVER = 104.5
# H_CLEAR = 2000
T_DELIVER_PRE = 0.2
T_DELIVER_POST = 0.2

# Capping
X_CAPPING = 51.25
Y_CAPPING_DOWN_1 = 22
Y_CAPPING_DOWN_2 = 0
Y_CAPPING_UP = 65
T_RAIL_FIXED_JACK = .7
T_RAIL_MOVING_JACK = .7


async def main(system, ALL_NODES_DICT):
    robot_1 = ALL_NODES_DICT['Robot 1']
    stations = [ALL_NODES_DICT['Station %d' % (i + 1)] for i in range(1)]
    rail = ALL_NODES_DICT['Rail']
    all_nodes = stations + [robot_1, rail]

    # All Nodes Ready?
    for node in all_nodes:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    # print('Home Everything')
    # print('Home Everything - 0- valves')
    # await run_stations(stations, lambda x: x.set_valves([0] * 5))
    # await robot_1.set_valves([0] * 10)
    await rail.set_valves([0] * 2)
    #
    # print('Home Everything - 1- stations')
    # await run_stations(stations, lambda s: s.home())
    #
    # print('Home Everything - 2- robot')
    # await robot_1.home()
    #
    # print('Home Everything - 3- rail')
    await rail.home()
    # await rail.goto(D_STANDBY, feed=6000)

    STATUS = {
        'stations_full': False,
        'robots_full': False,
    }

    ''' station standalone test'''
    # await run_stations(stations, lambda x: x.set_valves([0, 0, 0, 1]))
    # input('?')
    # await do_station(stations, robot_1, rail, all_nodes, STATUS)
    # return

    ''' rail standalone test'''
    while True:
        input('again?')
        t0 = time.time()
        await do_rail(stations, robot_1, rail, all_nodes, STATUS)
        print(time.time() - t0)


# async def speed_test_station(self):
#     try:
#         node = ALL_NODES_DICT['Station 1']
#         print(1)
#         while 'm4-main' not in node.get_status().get('data', {}):
#             await asyncio.sleep(.01)
#         print(2)
#         await asyncio.sleep(2)
#         await node.send_command({'verb': 'home', 'axis': 3}),
#
#         t0 = time.time()
#         await node.send_command(
#             ({'verb': 'move_motors', 'moves': [[], [], [], [21500, 300, 1, 1]]}))
#         t1 = time.time()
#         print(t1 - t0)
#
#         await asyncio.sleep(.5)
#         await node.send_command(
#             ({'verb': 'move_motors', 'moves': [[], [], [], [1, 300, 1, 1]]}))
#     except:
#         print(traceback.format_exc())
#
#
# async def speed_test_robot(self):
#     try:
#
#         node = ALL_NODES_DICT['Robot 1']
#         print(1)
#         while 'm1' not in node.get_status().get('data', {}):
#             await asyncio.sleep(.01)
#         print(2)
#         await node.send_command({'verb': 'home', 'axis': 0}),
#
#         t0 = time.time()
#         await node.send_command(
#             ({'verb': 'move_motors', 'moves': [[9000, 300, 1, 1]]}))
#         t1 = time.time()
#         print(t1 - t0)
#
#         await asyncio.sleep(.5)
#         await node.send_command(
#             ({'verb': 'move_motors', 'moves': [[1, 300, 1, 1]]}))
#     except:
#         print(traceback.format_exc())


async def do_rail(stations, robot_1, rail, all_nodes, STATUS):
    data = {}
    data['D_STANDBY'] = D_STANDBY
    data['D_MIN'] = data['D_STANDBY'] - 125
    data['D_MAX'] = data['D_MIN'] + 25 * 10

    data['FEED_RAIL_FREE'] = 9000
    data['FEED_RAIL_INTACT'] = 6000
    data['T_RAIL_JACK1'] = .4
    data['T_RAIL_JACK2'] = .7

    c = '''
; rail backward
G1 Z%(D_MIN).2f F%(FEED_RAIL_FREE)d

; change jacks to moving
M100 ({out9: 1, out10: 0})
G4 P%(T_RAIL_JACK1).2f
M100 ({out9: 1, out10: 1})
G4 P%(T_RAIL_JACK2).2f

; rail forward
G1 Z%(D_MAX).2f F%(FEED_RAIL_INTACT)d

; change jacks to moving
M100 ({out9: 1, out10: 0})
G4 P%(T_RAIL_JACK1).2f
M100 ({out9: 0, out10: 0})
G4 P%(T_RAIL_JACK2).2f

; rail park
G1 Z%(D_STANDBY).2f F%(FEED_RAIL_FREE)d
''' % data
    print(await rail.send_command_raw(c))


def run_stations(stations, func):
    tasks = []
    for station in stations:
        tasks.append(func(station))

    return asyncio.gather(*tasks)
