import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    feeder = await gather_feeder(system, ALL_NODES)
    print('feeder ready')

    await feeder.set_valves([0] * 14)
    await feeder.home()

    await feeder.send_command({'verb': 'feeder_process'})

    # t0 = time.time()
    # for i in range(10):
    #     await feeder.send_command_raw('G1 Z41 F6000')
    #     await feeder.send_command_raw('G1 Z16 F6000')
    # print(time.time() - t0)


async def gather_feeder(system, ALL_NODES):
    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]

    while not feeder.ready_for_command():
        await asyncio.sleep(.01)

    return feeder
