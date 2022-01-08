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

    t0 = time.time()
    z0 = 100

    j0 = 60000
    f0 = 25000

    j1 = 10000
    f1 = 35000

    await feeder.send_command_raw('{z:{jm: %d}}' % j0)
    await asyncio.sleep(.5)

    for i in range(10):
        # await asyncio.sleep(.1)
        await feeder.G1(z=z0 + i * 25, feed=f0)

    await feeder.send_command_raw('{z:{jm: %d}}' % j1)
    await asyncio.sleep(.5)

    await feeder.G1(z=700, feed=f1)
    await asyncio.sleep(.5)
    await feeder.G1(z=100, feed=f1)
    t1 = time.time()
    print(t1 - t0 - 1)
