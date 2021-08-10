import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    feeder, rail = await gather_feeder(system, ALL_NODES)
    print('nodes ready')

    # await feeder.set_valves([0] * 14)
    # await rail.set_valves([0, 0])
    # await rail.home()
    # await feeder.send_command_raw('{m1:100}')

    await feeder.set_valves([1])
    await rail.set_valves([1, 0])
    await asyncio.sleep(1)
    await rail.set_valves([1, 1])
    await asyncio.sleep(1)
    await rail.G1(z=502, feed=6000)
    # await asyncio.sleep(1)
    # await rail.set_valves([1, 0])
    # await asyncio.sleep(1)
    # await rail.set_valves([0, 0])
    # await feeder.set_valves([0])
    # await asyncio.sleep(1)
    # await rail.G1(z=.05, feed=500)

    # await rail.set_valves([0, 0])
    # await rail.G1(z=502, feed=1000)

    return
    # await feeder.send_command({'verb': 'feeder_process'})


async def gather_feeder(system, ALL_NODES):
    for node in ALL_NODES:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    return feeder, rail
