import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    feeder, rail = await gather_feeder(system, ALL_NODES)
    print('nodes ready')

    await feeder.home()

    # for i in range(1, 10):
    #     await feeder.send_command_raw('{m%d:0}' % i)  # Holder Downstream
    # await feeder.set_valves([0] * 14)
    # await rail.set_valves([0] * 10)
    # await asyncio.sleep(1)
    # await rail.home()
    # for i in range(2):
    #     await rail.G1(z=450, feed=8000)
    #     await asyncio.sleep(.5)
    #     await rail.G1(z=10, feed=8000)
    #     await asyncio.sleep(.5)


async def gather_feeder(system, ALL_NODES):
    for node in ALL_NODES:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    return feeder, rail
