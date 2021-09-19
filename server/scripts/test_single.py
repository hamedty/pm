import time
import asyncio
from .main import *
import traceback
import aioconsole
from .recipe import *
from scripts import recipe


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    # f = 100000
    # await feeder.home()
    # await feeder.G1(z=10, feed=f)
    # await feeder.G1(z=719, feed=f)
    # await feeder.send_command_raw('{z:{jm:100}}')
    # await feeder.G1(z=16, feed=f)
    # await feeder.send_command_raw('{z:{jm:10000}}')
    # for i in range(10):
    #     await feeder.G1(z=16 + i * 25, feed=f)

    # robot = robots[0]
    # f = 60000
    # await robot.home()
    # await robot.G1(x=20, feed=f)
    # await robot.G1(x=300, feed=f)
    # await robot.G1(x=20, feed=f)
