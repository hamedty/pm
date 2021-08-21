import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    feeder, rail = await gather_feeder(system, ALL_NODES)
    print('nodes ready')

    for i in range(1, 10):
        await feeder.send_command_raw('{m%d:0}' % i)  # Holder Downstream

    await rail.home()
    await rail.G1(z=50, feed=5000)
    # await rail.send_command_raw('G1 Z50.00 F5000')


async def gather_feeder(system, ALL_NODES):
    for node in ALL_NODES:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    return feeder, rail
