import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    N = 3
    feeder, rail = await gather_feeder(system, ALL_NODES)

    await feeder.set_valves([0] * 14)
    await rail.set_valves([0, 0])

    if not feeder.homed:
        for i in range(1, 10):
            await feeder.send_command_raw('{m%d:0}' % i)  # Holder Downstream
        await feeder.home()
        await rail.home()
    else:
        await feeder.G1(z=16, feed=1000)  # Holder Downstream
        await rail.G1(z=2, feed=6000)  # Holder Downstream

    await feeder.send_command_raw('{m2:15, m3:15}')  # Holder Downstream
    # Holder Upstream - Lift and long
    # await feeder.send_command_raw('{m4:60, m7:130}')
    await feeder.send_command_raw('{m5:100, m6:161}')  # Cartridge Conveyor

    await feeder.send_command({'verb': 'feeder_process', 'N': N})

    # hand over
    await rail.set_valves([1, 0])
    await asyncio.sleep(.6)
    await feeder.set_valves([None, 0])
    await rail.set_valves([1, 1])
    await asyncio.sleep(.6)

    await rail.G1(z=251, feed=6000)  # Holder Downstream
    await rail.set_valves([1, 0])
    await asyncio.sleep(.6)
    await rail.set_valves([0, 0])
    await asyncio.sleep(.6)

    # await feeder.home()
    # await feeder.send_command_raw('G1 Y90 F50000')
    # await asyncio.sleep(1)
    # await feeder.send_command_raw('G1 Y5 F50000')
    # await feeder.send_command_raw('G38.3 Y-100 F5000')
    # await feeder.send_command_raw('G10 L20 P1 Y0')
    # await feeder.send_command_raw('G1 Y90 F50000')


async def gather_feeder(system, ALL_NODES):
    for node in ALL_NODES:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    return feeder, rail
