import asyncio

from node import ALL_NODES

NODE = ALL_NODES[0]


async def main():
    await NODE.connect()
    # await NODE.send_command({'verb': 'create_arduino'})
    # await NODE.send_command_reset_arduino()
    await NODE.send_command_config_arduino()

    # Homing
    # await NODE.send_command({'verb': 'set_valves', 'valves': [0, 0, 0, 0, 0, 0], })
    # await asyncio.sleep(.25)
    await NODE.send_command({'verb': 'home', 'axis': 3, })
    # while True:
    #     await NODE.send_command({'verb': 'set_valves', 'valves': [1, 1, 0, 1, 1, 0], })
    #     await asyncio.sleep(1)
    #     await NODE.send_command({'verb': 'set_valves', 'valves': [0, 0, 0, 0, 0, 0], })
    #     await asyncio.sleep(1)

    # await asyncio.sleep(1)
    await NODE.send_command({'verb': 'move_motors', 'moves': [
        [10000, 250, 0],
        [10000, 250, 0],
        [10000, 250, 0],
        [000, 250, 1],
    ]})
    # await NODE.send_command({'verb': 'move_motors', 'moves': [
    #     [000, 250, 0],
    #     [000, 250, 0],
    #     [000, 250, 0],
    #     [-10000, 250, 1],
    # ]})

asyncio.run(main())
# set valves 0
# home x1
# home x0
# 4k up (4.5)
# fwd 5k + 10k + 5+5 -3 + 1 -.5 - .3
# close jacks (1,1)
# 11
