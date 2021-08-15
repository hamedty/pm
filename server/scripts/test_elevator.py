import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    feeder, rail = await gather_feeder(system, ALL_NODES)
    print('nodes ready')

    # for i in range(1, 10):
    #     await feeder.send_command_raw('{m%d:0}' % i)  # Holder Downstream
    #
    # await feeder.send_command_raw('{m2:15, m3:15}')  # Holder Downstream
    # # Holder Upstream - Lift and long
    # # await feeder.send_command_raw('{m4:60, m7:130}')
    # await feeder.send_command_raw('{m4:60, m7:00}')
    await rail.home()
    await rail.G1(z=200, feed=10000)


async def gather_feeder(system, ALL_NODES):
    for node in ALL_NODES:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    return feeder, rail
