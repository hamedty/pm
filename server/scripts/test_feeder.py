import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    feeder = await gather_feeder(system, ALL_NODES)

    await feeder.set_valves([0] * 14)
    await feeder.send_command_raw('{m2:15, m3:15}')  # Holder Downstream
    # await feeder.send_command_raw('{m4:60, m7:130}')  # Holder Upstream - Lift and long
    if not feeder.homed:
        await feeder.home()
    else:
        await feeder.G1(z=16, feed=1000)  # Holder Downstream

    await feeder.send_command({'verb': 'feeder_process'})


async def gather_feeder(system, ALL_NODES):
    for node in ALL_NODES:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]

    return feeder
