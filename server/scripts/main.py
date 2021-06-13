import time
import asyncio


D_STANDBY = 250
FEED_X = 8500
FEED_Y_UP = 8000
FEED_Y_DOWN = 9000
FEED_RAIL_FREE = 9000
FEED_RAIL_INTACT = 6000
FEED_Z_UP = 15000
FEED_Z_DOWN = 25000


async def main(system, ALL_NODES_DICT):
    robot_1 = ALL_NODES_DICT['Robot 1']
    stations = [ALL_NODES_DICT['Station %d' % (i + 1)] for i in range(1)]
    rail = ALL_NODES_DICT['Rail']
    all_nodes = stations + [robot_1, rail]

    # All Nodes Ready?
    for node in all_nodes:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    print('Home Everything')
    print('Home Everything - 0- valves')
    await run_stations(stations, lambda x: x.set_valves([0] * 5))
    await robot_1.set_valves([0] * 10)
    await rail.set_valves([0] * 2)

    print('Home Everything - 1- stations')
    await run_stations(stations, lambda s: s.home())

    print('Home Everything - 2- robot')
    await robot_1.home()

    print('Home Everything - 3- rail')
    # await rail.home()
    # await rail.goto(D_STANDBY, feed=FEED_RAIL_FREE)

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
    # while True:
    #     input('again?')
    #     t0 = time.time()
    #     await do_rail(stations, robot_1, rail, all_nodes, STATUS)
    #     print(time.time() - t0)

    while True:
        input('repeat?')
        t0 = time.time()
        await asyncio.gather(
            # do_station(stations, robot_1, rail, all_nodes, STATUS),
            do_rail_n_robots(stations, robot_1, rail, all_nodes, STATUS)
        )
        print('------------------------------')
        print('rail and robot:', time.time() - t0)
        t0 = time.time()
        await do_exchange(stations, robot_1, rail, all_nodes, STATUS)
        print('------------------------------')
        print('exchange:', time.time() - t0)


async def do_rail_n_robots(stations, robot_1, rail, all_nodes, STATUS):
    print('here')
    await do_robots_cap(stations, robot_1, rail, all_nodes, STATUS)
    # await do_rail(stations, robot_1, rail, all_nodes, STATUS)
    await do_robots_pickup(stations, robot_1, rail, all_nodes, STATUS)


async def do_exchange(stations, robot_1, rail, all_nodes, STATUS):
    print('deliver')

    data = {}
    data['X_INPUT'] = 375
    data['Y_INPUT_DOWN_1'] = 35
    data['Y_INPUT_UP'] = 55
    data['Y_INPUT_DOWN_3'] = 10
    data['Y_INPUT_DOWN_2'] = data['Y_INPUT_DOWN_3'] + 10

    data['FEED_X'] = FEED_X
    data['FEED_Y_UP'] = FEED_Y_UP
    data['FEED_Y_DOWN'] = FEED_Y_DOWN
    data['FEED_Y_PRESS'] = 3000

    data['T_INPUT_RELEASE'] = 0.5
    data['T_HOLDER_JACK_CLOSE'] = 0.5

    c = '''
    G1 X%(X_INPUT).2f F%(FEED_X)d
    G1 Y%(Y_INPUT_DOWN_1).2f F%(FEED_Y_DOWN)d
    M100 ({out1: 0, out2: 0, out3: 0, out4: 0, out5: 0})
    M100 ({out6: 0, out7: 0, out8: 0, out9: 0, out10: 0})
    G4 P%(T_INPUT_RELEASE).2f

    G1 Y%(Y_INPUT_UP).2f F%(FEED_Y_UP)d
    M100 ({out6: 1, out7: 1, out8: 1, out9: 1, out10: 1})
    G4 P%(T_HOLDER_JACK_CLOSE).2f
    G1 Y%(Y_INPUT_DOWN_2).2f F%(FEED_Y_DOWN)d
    G4 P.5
    G1 Y%(Y_INPUT_DOWN_3).2f F%(FEED_Y_PRESS)d
    ''' % data

    await robot_1.send_command_raw(c)

    data = {}

    data['Z_OUTPUT'] = 80
    data['Y_OUTPUT'] = 70
    data['Z_OUTPUT_SAFE'] = data['Z_OUTPUT'] - 20
    data['X_OUTPUT_SAFE'] = 280

    data['T_OUTPUT_GRIPP'] = 0.5
    data['T_OUTPUT_RELEASE'] = 0.5

    data['FEED_X'] = FEED_X
    data['FEED_Y_UP'] = FEED_Y_UP
    data['FEED_Z_DOWN'] = FEED_Z_DOWN
    data['FEED_Z_UP'] = FEED_Z_UP

    c = '''
    G1 Z%(Z_OUTPUT).2f F%(FEED_Z_DOWN)d
    ''' % data
    await run_stations(stations, lambda x: x.send_command_raw(c))

    c = '''
    G1 Y%(Y_OUTPUT).2f F%(FEED_Y_UP)d
    M100 ({out1: 1, out2: 1, out3: 1, out4: 1, out5: 1})
    ''' % data
    await robot_1.send_command_raw(c)

    await asyncio.sleep(data['T_OUTPUT_GRIPP'])

    c = '''
    M100 ({out1: 0})
    G4 P%(T_OUTPUT_RELEASE).2f
    G1 Z%(Z_OUTPUT_SAFE).2f F%(FEED_Z_UP)d
    ''' % data
    await run_stations(stations, lambda x: x.send_command_raw(c))

    c = '''
    G1 X%(X_OUTPUT_SAFE).2f F%(FEED_X)d
    ''' % data
    await robot_1.send_command_raw(c)

    # STATUS['robots_full'] = False
    STATUS['stations_full'] = True


async def do_station(stations, robot_1, rail, all_nodes, STATUS):
    if not STATUS['stations_full']:
        return

    align_holders = []
    for station in stations:
        align_holders.append(station.send_command(
            {'verb': 'align', 'component': 'holder', 'speed': 250}))
    align_holders = asyncio.gather(*align_holders)
    await align_holders

    print('prepare dosing')

    t0 = time.time()

    data = {}
    # go to aliging location
    data['H_ALIGNING'] = 230
    data['FEED_ALIGNING'] = 20000
    data['PAUSE_ALIGNING'] = 0.1

    # Fall
    data['PAUSE_FALL_DOSING'] = 0.1

    # Ready to push
    data['H_READY_TO_PUSH'] = data['H_ALIGNING'] - 5
    data['FEED_READY_TO_PUSH'] = 10000
    data['PAUSE_READY_TO_PUSH'] = 0.1

    # Push
    data['H_PUSH'] = 239
    data['FEED_PUSH'] = 2000
    data['PAUSE_PUSH'] = 0.1
    data['H_PUSH_BACK'] = data['H_PUSH'] - 5
    data['FEED_PUSH_BACK'] = 10000

    # Dance
    data['PAUSE_JACK_PRE_DANCE_1'] = 0.1
    data['PAUSE_JACK_PRE_DANCE_2'] = 0.1
    data['PAUSE_JACK_PRE_DANCE_3'] = 0.1
    data['H_PRE_DANCE'] = 246
    data['FEED_PRE_DANCE'] = 15000

    data['H_DANCE'] = data['H_PRE_DANCE'] - 8
    data['Y_DANCE'] = 360
    data['FEED_DANCE'] = 200000

    # Press
    data['PAUSE_PRESS1'] = 0.5
    data['PAUSE_PRESS2'] = 0.6

    # Dance Back
    data['PAUSE_JACK_PRE_DANCE_BACK'] = .3
    data['PAUSE_POST_DANCE_BACK'] = .3

    data['H_DANCE_BACK'] = data['H_PRE_DANCE']
    data['Y_DANCE_BACK'] = 0
    data['FEED_DANCE_BACK'] = data['FEED_DANCE']

    # Deliver
    data['H_DELIVER'] = 40
    data['FEED_DELIVER'] = 10000

    c = '''
; go to aligning position
G1 Z%(H_ALIGNING).2f F%(FEED_ALIGNING)d
G4 P%(PAUSE_ALIGNING).2f
''' % data

    await run_stations(stations, lambda s: s.send_command_raw(c))
    print(time.time() - t0)
    t0 = time.time()

    await run_stations(stations, lambda x: x.send_command({'verb': 'align', 'component': 'dosing', 'speed': 25000}, assert_success=True))
    print(time.time() - t0)
    t0 = time.time()

    c = '''
; release dosing
M100 ({out1: 0, out4: 0})
G4 P%(PAUSE_FALL_DOSING).2f

; ready to push
G1 Z%(H_READY_TO_PUSH).2f F%(FEED_READY_TO_PUSH)d
M100 ({out1: 1})
G4 P%(PAUSE_READY_TO_PUSH).2f

; push and come back
G1 Z%(H_PUSH).2f F%(FEED_PUSH)d
G4 P%(PAUSE_PUSH).2f
G1 Z%(H_PUSH_BACK).2f F%(FEED_PUSH_BACK)d

; prepare for dance
M100 ({out1: 0, out4: 1})
G4 P%(PAUSE_JACK_PRE_DANCE_1).2f
G1 Z%(H_PRE_DANCE).2f F%(FEED_PRE_DANCE)d
G4 P%(PAUSE_JACK_PRE_DANCE_2).2f
M100 ({out1: 1})
G4 P%(PAUSE_JACK_PRE_DANCE_3).2f

; dance
G1 Z%(H_DANCE).2f Y%(Y_DANCE).2f F%(FEED_DANCE)d

; press
M100 ({out1: 0, out2: 0, out4: 0, out5: 1})
G4 P%(PAUSE_PRESS1).2f
M100 ({out3: 1})
G4 P%(PAUSE_PRESS2).2f
M100 ({out3: 0})

; dance back
M100 ({out1: 1, out5: 0})
G4 P%(PAUSE_JACK_PRE_DANCE_BACK).2f
G1 Z%(H_DANCE_BACK).2f Y%(Y_DANCE_BACK).2f F%(FEED_DANCE_BACK)d
G4 P%(PAUSE_POST_DANCE_BACK).2f

; deliver
G1 Z%(H_DELIVER).2f F%(FEED_DELIVER)d
''' % data

    await run_stations(stations, lambda s: s.send_command_raw(c))
    print(time.time() - t0)

    return


async def do_robots_cap(stations, robot_1, rail, all_nodes, STATUS):
    if not STATUS['stations_full']:
        return

    print('Capping')

    X_CAPPING = 51.25
    Y_CAPPING_DOWN_1 = 22
    Y_CAPPING_DOWN_2 = 0
    Y_CAPPING_UP = 65
    T_RAIL_FIXED_JACK = .7
    T_RAIL_MOVING_JACK = .7
    X_PARK = 0
    Y_PARK = 0

    await robot_1.goto(x=X_CAPPING, feed=FEED_X)

    await rail.set_valves([1, 0])
    await asyncio.sleep(T_RAIL_MOVING_JACK)
    await rail.set_valves([1, 1])

    await robot_1.goto(y=Y_CAPPING_DOWN_1, feed=FEED_Y_DOWN)

    await rail.set_valves([1, 0])
    await asyncio.sleep(T_RAIL_FIXED_JACK)
    await rail.set_valves([0, 0])

    await robot_1.goto(y=Y_CAPPING_DOWN_2, feed=FEED_Y_DOWN)
    await robot_1.set_valves([0] * 10)
    await robot_1.goto(y=Y_CAPPING_UP, feed=FEED_Y_UP)

    await robot_1.goto(x=X_PARK, feed=FEED_X)
    await robot_1.goto(y=Y_PARK, feed=FEED_Y_DOWN)


async def do_robots_pickup(stations, robot_1, rail, all_nodes, STATUS):
    print('lets go grab input')

    data = {}
    data['Y_GRAB_IN_UP_1'] = 65
    data['X_GRAB_IN'] = 284.5
    data['Y_GRAB_IN_DOWN'] = 0
    data['Y_GRAB_IN_UP_2'] = data['Y_GRAB_IN_UP_1']

    data['FEED_Y_UP'] = FEED_Y_UP
    data['FEED_Y_DOWN'] = FEED_Y_DOWN
    data['FEED_X'] = FEED_X

    data['T_GRAB_IN'] = 0.5

    c = '''
G1 Y%(Y_GRAB_IN_UP_1).2f F%(FEED_Y_UP)d
G1 X%(X_GRAB_IN).2f F%(FEED_X)d
G1 Y%(Y_GRAB_IN_DOWN).2f F%(FEED_Y_DOWN)d

M100 ({out1: 1, out2: 1, out3: 1, out4: 1, out5: 1})
M100 ({out6: 1, out7: 1, out8: 1, out9: 1, out10: 1})
G4 P%(T_GRAB_IN).2f

G1 Y%(Y_GRAB_IN_UP_2).2f F%(FEED_Y_UP)d
''' % data
    await robot_1.send_command_raw(c)

    STATUS['robots_full'] = True


async def do_rail(stations, robot_1, rail, all_nodes, STATUS):
    data = {}
    data['D_STANDBY'] = D_STANDBY
    data['D_MIN'] = data['D_STANDBY'] - 125
    data['D_MAX'] = data['D_MIN'] + 25 * 10

    data['FEED_RAIL_FREE'] = FEED_RAIL_FREE
    data['FEED_RAIL_INTACT'] = FEED_RAIL_INTACT
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


def run_stations(stations, func):
    tasks = []
    for station in stations:
        tasks.append(func(station))

    return asyncio.gather(*tasks)
