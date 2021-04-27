import asyncio

from node import ALL_NODES

NODE = ALL_NODES[0]


async def main():
    await NODE.connect()
    # await NODE.send_command({'verb': 'create_arduino'})
    # await NODE.send_command_reset_arduino()
    # await NODE.send_command_config_arduino()
    # await NODE.send_command({'verb': 'set_valves', 'valves': [1, 1], })
    await NODE.send_command({'verb': 'home', 'axis': 1, })
    # await NODE.send_command({'verb': 'home', 'axis': 0, })
    # await asyncio.sleep(1)
    await NODE.send_command({'verb': 'move_motors', 'moves': [
        [000, 250, 0],
        [000, 250, 0]
    ]})

asyncio.run(main())
