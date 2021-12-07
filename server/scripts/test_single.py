import time
from .main import *
import asyncio
import traceback
import aioconsole
from .recipe import *
from scripts import recipe
from node import ALL_NODES_DICT


async def main(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)

    # await feeder.set_motors((4, 8), (7, 11))
    # await feeder.set_motors((7, 11))
    # while True:
    #     await feeder.set_valves([None, None, 1])
    #     await asyncio.sleep(0.25)
    #     await feeder.set_valves([None, None, 0])
    #     await asyncio.sleep(3)

    # for i in range(40 + 1):
    #     await feeder.set_valves([0] * 6 + [i % 2])
    #     await asyncio.sleep(.3)
    # stations = stations[:3]
    # for i in range(10):
    #     await asyncio.gather(*[s.G1(z=200, feed=15000) for s in stations])
    #     await asyncio.gather(*[s.G1(z=10, feed=10000) for s in stations])

    await dosing_feeder.set_motors(feeder, (9, 5))
