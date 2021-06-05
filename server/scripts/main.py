import asyncio

D_STANDBY = 40000
X_PARK = 0
Y_PARK = 8250

# Grab
X_GRAB_IN = 22750
Y_GRAB_IN_UP_1 = 6250
Y_GRAB_IN_DOWN = 0
Y_GRAB_IN_UP_2 = Y_GRAB_IN_UP_1
T_GRAB_IN = 1

# Place In
X_PLACE_IN = 29850
Y_PLACE_IN = 1600
Y_PLACE_IN_PRESS = 400
Y_PLACE_IN_COMEOUT = Y_PLACE_IN
T_PLACE_IN_FALL = 0.5
T_PLACE_IN_JACK_CLOSE = 0.5
T_PLACE_IN_PRESS = 0.2

# Start Station Process
X_MOVE_SAFE_STATION = 23000


async def main(system, ALL_NODES_DICT):
    await asyncio.sleep(1)

    robot_1 = ALL_NODES_DICT['Robot 1']
    stations = [ALL_NODES_DICT['Station %d' % (i + 1)] for i in range(5)]
    rail = ALL_NODES_DICT['Rail']
    all_nodes = stations + [robot_1, rail]
    for node in all_nodes:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    # print('Home Everything')
    # print('Home Everything - 1- robot')
    # await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 10}, assert_success=True)
    # await robot_1.send_command({'verb': 'home', 'axis': 1}, assert_success=True)
    # await robot_1.send_command({'verb': 'home', 'axis': 0}, assert_success=True)
    #
    # print('Home Everything - 2- stations and rail together')
    # tasks = []
    # for station in stations:
    #     tasks.append(station.send_command(
    #         {'verb': 'set_valves', 'valves': [0] * 5}, assert_success=True))
    #     tasks.append(station.send_command(
    #         {'verb': 'home', 'axis': 3}, assert_success=True))
    #
    # # tasks.append(rail.send_command(
    # # {'verb': 'home', 'axis': 0}, assert_success=True))
    #
    # await asyncio.gather(*tasks)
    # # await rail.goto(D_STANDBY)

    while True:
        # # await rail.is_homed()
        #
        # print('Take robot to starting point')
        # await robot_1.goto(y=Y_PARK)
        # await robot_1.goto(x=X_PARK)
        #
        # input('continue?')
        # print('lets go grab input')
        # await robot_1.goto(y=Y_GRAB_IN_UP_1)
        # await robot_1.goto(x=X_GRAB_IN)
        # await robot_1.goto(y=Y_GRAB_IN_DOWN)
        #
        # await robot_1.send_command(
        #     {'verb': 'set_valves', 'valves': [1] * 10})
        # await asyncio.sleep(T_GRAB_IN)
        #
        # await robot_1.goto(y=Y_GRAB_IN_UP_2)

        # print('put input into station')
        # tasks = []
        # for station in stations:
        #     tasks.append(station.send_command(
        #         {'verb': 'set_valves', 'valves': [0, 0, 0, 1]}, assert_success=True))
        #
        # tasks.append(robot_1.goto(x=X_PLACE_IN))
        # await asyncio.gather(*tasks)
        #
        # await robot_1.goto(y=Y_PLACE_IN)
        # await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 10})
        # await asyncio.sleep(T_PLACE_IN_FALL)

        # print('press holder in')
        # await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 5 + [1] * 5})
        # await asyncio.sleep(T_PLACE_IN_JACK_CLOSE)
        # await robot_1.goto(y=Y_PLACE_IN_PRESS)
        # await asyncio.sleep(T_PLACE_IN_PRESS)
        # await robot_1.goto(y=Y_PLACE_IN_COMEOUT)
        # await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 10})

        # print('Move back for station to work')
        # move_robot_back = asyncio.create_task(
        #     robot_1.goto(x=X_MOVE_SAFE_STATION))
        #
        # align_holders = []
        # for station in stations:
        #     align_holders.append(station.send_command(
        #         {'verb': 'align', 'component': 'holder'}))
        # align_holders = asyncio.gather(*align_holders)
        #
        # await move_robot_back

        print('prepare dosing')
        # H_ALIGNING = 21500
        # H_PUSH = 23000
        # H_PUSH_BACK = H_PUSH - 500
        # H_GRIPP = 23700

        # await run_stations(stations, lambda s: s.goto('H_ALIGNING'))
        # await station_1.send_command({'verb': 'align', 'component': 'dosing'})
        await run_stations(stations, lambda x: x.send_command({'verb': 'align', 'component': 'dosing'}))

        return
        # await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [1]}))
        await station_1.send_command({'verb': 'set_valves', 'valves': [0, None, 0, 0]})
        await asyncio.sleep(.3)
        await station_1.send_command({'verb': 'set_valves', 'valves': [1]})
        await asyncio.sleep(.2)
        await station_1.send_command({'verb': 'move_motors', 'moves': [[], [], [], [H_PUSH, 150, 1, 1]]})
        await asyncio.sleep(.2)
        await station_1.send_command({'verb': 'move_motors', 'moves': [[], [], [], [H_PUSH_BACK, 150, 1, 1]]})
        await station_1.send_command({'verb': 'set_valves', 'valves': [0, None, 0, 1]})
        await station_1.send_command({'verb': 'move_motors', 'moves': [[], [], [], [H_GRIPP, 150, 1, 1]]})
        await asyncio.sleep(.1)
        await station_1.send_command({'verb': 'set_valves', 'valves': [1, None, 0, 1]})
        await asyncio.sleep(.3)
        await station_1.send_command_scenario({'verb': 'dance', 'value': 100})
        await station_1.send_command({'verb': 'set_valves', 'valves': [0, 0, 0, 0, 1]})
        # await align_holders

        print('press')
        H_DELIVER = 4000
        X_DELIVER = 59800 / 2
        Y_DELIVER = 16700 / 2
        H_CLEAR = 2000
        await asyncio.sleep(.1)
        await station_1.send_command({'verb': 'set_valves', 'valves': [0, 0, 1]})
        await asyncio.sleep(1)
        await station_1.send_command({'verb': 'set_valves', 'valves': [0, 0, 0]})
        await asyncio.sleep(.2)
        await station_1.send_command({'verb': 'set_valves', 'valves': [1, 0, 0, 0, 0]})
        await asyncio.sleep(.2)
        await station_1.send_command_scenario({'verb': 'dance', 'value': -100, 'extra_m3': -100})
        await asyncio.sleep(.2)
        await station_1.send_command({'verb': 'move_motors', 'moves': [[], [], [], [H_DELIVER, 150, 1, 1]]})
        await robot_1.goto(y=Y_DELIVER)
        await robot_1.goto(x=X_DELIVER)
        await robot_1.send_command({'verb': 'set_valves', 'valves': [1]})
        await asyncio.sleep(.2)
        await station_1.send_command({'verb': 'set_valves', 'valves': [0]})
        await station_1.send_command({'verb': 'move_motors', 'moves': [[], [], [], [H_CLEAR, 150, 1, 1]]})

        print('Capping')
        X_CAPPING = 8200 / 2
        Y_CAPPING_1 = 7000 / 2

        await robot_1.goto(x=X_CAPPING)
        await robot_1.goto(y=Y_CAPPING_1)
        await robot_1.send_command({'verb': 'set_valves', 'valves': [0]})


def run_stations(stations, func):
    tasks = []
    for station in stations:
        tasks.append(func(station))

    return asyncio.gather(*tasks)
