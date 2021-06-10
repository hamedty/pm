import asyncio


# Grab
X_GRAB_IN = 285
Y_GRAB_IN_UP_1 = 78
Y_GRAB_IN_DOWN = 0
Y_GRAB_IN_UP_2 = Y_GRAB_IN_UP_1
T_GRAB_IN = .5


# D_STANDBY = 40000
X_PARK = 0
Y_PARK = 3000
# D_MIN = 20000
# D_MAX = 24000
T_RAIL_FIXED_JACK = 0.7
T_RAIL_MOVING_JACK = 0.7
# Grab
X_GRAB_IN = 284.5
Y_GRAB_IN_UP_1 = 78
Y_GRAB_IN_DOWN = 0
Y_GRAB_IN_UP_2 = Y_GRAB_IN_UP_1
T_GRAB_IN = .5

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
Y_MOVE_SAFE_STATION = Y_GRAB_IN_UP_1
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
Y_CAPPING_UP = Y_GRAB_IN_UP_1


async def test(system, ALL_NODES_DICT):
    robot_1 = ALL_NODES_DICT['Robot 1']
    stations = [ALL_NODES_DICT['Station %d' % (i + 1)] for i in range(1)]
    rail = None  # ALL_NODES_DICT['Rail']
    all_nodes = stations + [robot_1]  # , rail]
    for node in all_nodes:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    print('Home Everything')
    print('Home Everything - 0- valves')
    await run_stations(stations, lambda x: x.set_valves([0] * 5))
    # await robot_1.set_valves([0] * 10)
    # await rail.send_command({'verb': 'set_valves', 'valves': [0] * 2}, assert_success=True)

    print('Home Everything - 1- stations')
    await run_stations(stations, lambda s: s.home())

    print('Home Everything - 2- robot')
    # await robot_1.home()

    print('Home Everything - 3- rail')
    # await rail.send_command({'verb': 'home', 'axis': 0}, assert_success=True)
    # await rail.goto(D_STANDBY)

    '''
    Remove this:
    '''
    await run_stations(stations, lambda x: x.set_valves([0, 0, 0, 1]))
    input('?')

    await do_station(stations, robot_1, rail, all_nodes)
    return
    while True:
        # input('repeat?')
        # await rail.is_homed()

        print('lets go grab input')

        await robot_1.goto(y=Y_GRAB_IN_UP_1)
        await robot_1.goto(x=X_GRAB_IN)
        await robot_1.goto(y=Y_GRAB_IN_DOWN)
        await robot_1.set_valves([1] * 10)
        await asyncio.sleep(T_GRAB_IN)
        await robot_1.goto(y=Y_GRAB_IN_UP_2)

        print('put input into station')
        tasks = []
        for station in stations:
            tasks.append(station.set_valves([0, 0, 0, 1]))

        tasks.append(robot_1.goto(x=X_PLACE_IN))
        await asyncio.gather(*tasks)

        await robot_1.goto(y=Y_PLACE_IN)
        await robot_1.set_valves([0] * 10)
        await asyncio.sleep(T_PLACE_IN_FALL)

        print('press holder in')
        await robot_1.set_valves([0] * 5 + [1] * 5)
        await asyncio.sleep(T_PLACE_IN_JACK_CLOSE)
        await robot_1.goto(y=Y_PLACE_IN_PRESS)
        await asyncio.sleep(T_PLACE_IN_PRESS)
        await robot_1.goto(y=Y_PLACE_IN_COMEOUT)
        await robot_1.set_valves([0] * 10)

        print('Move back for station to work')
        await robot_1.goto(x=X_MOVE_SAFE_STATION)

        await asyncio.gather(
            do_station(stations, robot_1, rail, all_nodes),
            do_rail(stations, robot_1, rail, all_nodes)
        )
        return

        print('deliver')
        # await run_stations(stations, lambda s: s.goto(H_DELIVER))
        await robot_1.goto(y=Y_DELIVER)
        await robot_1.goto(x=X_DELIVER)
        await robot_1.set_valves([1] * 5)
        await asyncio.sleep(T_DELIVER_PRE)
        # await run_stations(stations, lambda x: x.set_valves([0]))
        await asyncio.sleep(T_DELIVER_POST)
        # await run_stations(stations, lambda s: s.goto(H_CLEAR))

        print('Capping')

        await robot_1.goto(x=X_CAPPING)

        # await rail.set_valves([0, 1])
        await asyncio.sleep(T_RAIL_MOVING_JACK)
        # await rail.set_valves([1, 1])

        await robot_1.goto(y=Y_CAPPING_DOWN_1)

        # await rail.set_valves([0, 1])
        await asyncio.sleep(T_RAIL_FIXED_JACK)
        # await rail.set_valves([0, 0])

        await robot_1.goto(y=Y_CAPPING_DOWN_2)
        await robot_1.set_valves([0] * 10)
        await robot_1.goto(y=Y_CAPPING_UP)
        print('end of loop')

        return


async def do_station(stations, robot_1, rail, all_nodes):
    # align_holders = []
    # for station in stations:
    #     align_holders.append(station.send_command(
    #         {'verb': 'align', 'component': 'holder', 'speed': 250}))
    # align_holders = asyncio.gather(*align_holders)
    # await align_holders
    print('prepare dosing')

    import time
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
    data['H_PUSH'] = 240
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
    data['FEED_DANCE'] = 10000

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
    print(c)
    await run_stations(stations, lambda s: s.send_command_raw(c))
    print(time.time() - t0)

    return


async def do_rail(stations, robot_1, rail, all_nodes):
    await robot_1.goto(y=Y_MOVE_SAFE_STATION)
    await robot_1.goto(x=X_PARK)
    await robot_1.goto(y=Y_PARK)

    # await rail.goto(D_MIN)
    #
    # await rail.send_command({'verb': 'set_valves', 'valves': [0, 1]})
    # await asyncio.sleep(T_RAIL_MOVING_JACK)
    # await rail.send_command({'verb': 'set_valves', 'valves': [1, 1]})
    # await asyncio.sleep(T_RAIL_FIXED_JACK)
    #
    # await rail.goto(D_MAX)
    #
    # await rail.send_command({'verb': 'set_valves', 'valves': [0, 1]})
    # await asyncio.sleep(T_RAIL_FIXED_JACK)
    # await rail.send_command({'verb': 'set_valves', 'valves': [0, 0]})
    # await asyncio.sleep(T_RAIL_MOVING_JACK)
    #
    # await rail.goto(D_STANDBY)


def run_stations(stations, func):
    tasks = []
    for station in stations:
        tasks.append(func(station))

    return asyncio.gather(*tasks)
