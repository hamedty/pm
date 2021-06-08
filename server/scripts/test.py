import asyncio


async def test(system, ALL_NODES_DICT):
    station = ALL_NODES_DICT['Station 1']

    while not station.ready_for_command():
        await asyncio.sleep(.01)

    await station.set_valves([0] * 6)
    await station.send_command_raw('G54')
    print('salam')
    # await station.home()
    # await station.set_valves([1, 1])

    await station.send_command(
        {'verb': 'align', 'component': 'holder', 'speed': 25000})

    return

    await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [0] * 5}))
    await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 10}, assert_success=True)
    await rail.send_command({'verb': 'set_valves', 'valves': [0] * 2}, assert_success=True)

    print('Home Everything - 1- stations')
    await run_stations(stations, lambda s: s.send_command({'verb': 'home', 'axis': 3}, assert_success=True))

    print('Home Everything - 2- robot')
    await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 10}, assert_success=True)
    await robot_1.move_all_the_way_up()

    await robot_1.send_command({'verb': 'home', 'axis': 1}, assert_success=True)
    await robot_1.send_command({'verb': 'home', 'axis': 0}, assert_success=True)
