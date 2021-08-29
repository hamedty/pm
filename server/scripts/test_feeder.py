import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    print('test feeder started')

    N = 10

    feeder, rail = await gather_feeder(system, ALL_NODES)

    # Homing
    await asyncio.gather(
        feeder.home(),
        rail.home()
    )

    print('nodes ready and homed')

    await system.system_running.wait()

    # PWM Motors
    await feeder.set_motors(
        (2, 4), (3, 3),  # Holder Downstream
        (1, 23), (4, 8), (7, 46),  # Holder Upstream - Lift and long conveyor
        (6, 32),  # Cartridge Conveyor
    )
    print('pwm motors started ')

    while True:
        # phase 1
        await system.system_running.wait()
        await asyncio.gather(
            feeder1(feeder, N),  # Fill
            rail1(rail, N)  # come back to pick up
        )

        # hand over
        await system.system_running.wait()
        await rail.set_valves([1, 0])
        await asyncio.sleep(1)
        await feeder.set_valves([None, 0])
        await rail.set_valves([1, 1])
        await asyncio.sleep(1)

        await system.system_running.wait()
        await rail.G1(z=25 * N, feed=8000)
        # await rail.send_command_raw('G1 Z%d F1000' % (25 * N + 1))

        # phase 2
        await system.system_running.wait()
        await asyncio.gather(
            feeder2(feeder, N),  # come back
            rail2(rail, N)  # tarnsfer
        )


async def feeder1(feeder, N):
    await feeder.send_command({'verb': 'feeder_process', 'N': N})
    print('feeder process done')


async def rail1(rail, N):
    await rail.G1(z=0, feed=6000)
    # await rail.send_command_raw('G1 Z1 F1000')
    print('rail is back')


async def feeder2(feeder, N):
    await feeder.G1(z=16, feed=4000)
    print('feeder is back')


async def rail2(rail, N):
    await rail.set_valves([1, 0])
    await asyncio.sleep(1)
    await rail.set_valves([0, 0])
    await asyncio.sleep(1)
    print('everything done')


async def gather_feeder(system, ALL_NODES):
    for node in ALL_NODES:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    return feeder, rail
