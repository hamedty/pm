async def speed_test_station(self):
    try:
        node = ALL_NODES_DICT['Station 1']
        print(1)
        while 'm4-main' not in node.get_status().get('data', {}):
            await asyncio.sleep(.01)
        print(2)
        await asyncio.sleep(2)
        await node.send_command({'verb': 'home', 'axis': 3}),

        t0 = time.time()
        await node.send_command(
            ({'verb': 'move_motors', 'moves': [[], [], [], [21500, 300, 1, 1]]}))
        t1 = time.time()
        print(t1 - t0)

        await asyncio.sleep(.5)
        await node.send_command(
            ({'verb': 'move_motors', 'moves': [[], [], [], [1, 300, 1, 1]]}))
    except:
        print(traceback.format_exc())


async def speed_test_robot(self):
    try:

        node = ALL_NODES_DICT['Robot 1']
        print(1)
        while 'm1' not in node.get_status().get('data', {}):
            await asyncio.sleep(.01)
        print(2)
        await node.send_command({'verb': 'home', 'axis': 0}),

        t0 = time.time()
        await node.send_command(
            ({'verb': 'move_motors', 'moves': [[9000, 300, 1, 1]]}))
        t1 = time.time()
        print(t1 - t0)

        await asyncio.sleep(.5)
        await node.send_command(
            ({'verb': 'move_motors', 'moves': [[1, 300, 1, 1]]}))
    except:
        print(traceback.format_exc())


async def move_rail(self):
    X_PARK = 40000
    X1 = 20000
    X2 = 60000  # 24000
    DELAY_MOTOR = .001
    DELAY_FIXED_JACK = 0.7
    DELAY_MOVING_JACK = 0.7

    try:
        node = ALL_NODES_DICT['Rail']
        print(1)
        while 'm' not in node.get_status().get('data', {}):
            await asyncio.sleep(.01)

        await node.send_command({'verb': 'set_valves', 'valves': [0, 0]})
        await asyncio.sleep(DELAY_FIXED_JACK)
        # await node.send_command({'verb': 'home', 'axis': 0}),
        await node.send_command(({'verb': 'move_motors', 'moves': [[40000, 300, 1, 1]]}))
        await asyncio.sleep(DELAY_MOTOR)

        while True:
            for i in range(20):
                await node.send_command(({'verb': 'move_motors', 'moves': [[X1, 300, 1, 1]]}))
                await asyncio.sleep(DELAY_MOTOR)

                await node.send_command({'verb': 'set_valves', 'valves': [0, 1]})
                await asyncio.sleep(DELAY_MOVING_JACK)

                await node.send_command({'verb': 'set_valves', 'valves': [1, 1]})
                await asyncio.sleep(DELAY_FIXED_JACK)

                await node.send_command(({'verb': 'move_motors', 'moves': [[X2, 300, 1, 1]]}))
                await asyncio.sleep(DELAY_MOTOR)

                await node.send_command({'verb': 'set_valves', 'valves': [0, 1]})
                await asyncio.sleep(DELAY_FIXED_JACK)

                await node.send_command({'verb': 'set_valves', 'valves': [0, 0]})
                await asyncio.sleep(DELAY_MOVING_JACK)

                await node.send_command(({'verb': 'move_motors', 'moves': [[X_PARK, 300, 1, 1]]}))
                await asyncio.sleep(DELAY_MOTOR)
            input('repeat?')

        # t0 = time.time()
        # t1 = time.time()
        # print(t1 - t0)
    except:
        print(traceback.format_exc())
