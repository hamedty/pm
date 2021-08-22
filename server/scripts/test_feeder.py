import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    print('test feeder started')

    N = 10

    feeder, rail = await gather_feeder(system, ALL_NODES)

    # Homing
    await feeder.set_valves([0] * 14)
    await rail.set_valves([0, 0])
    await feeder.set_motors()

    await asyncio.gather(
        feeder.home(),
        rail.home()
    )

    print('nodes ready and homed')
    await system.system_running.wait()

    # PWM Motors
    await feeder.set_motors(
        (2, 25), (3, 30),  # Holder Downstream
        (4, 38), (7, 300),  # Holder Upstream - Lift and long conveyor
        (6, 160),  # Cartridge Conveyor
    )
    print('pwm motors started ')

    while True:
        await system.system_running.wait()

        await feeder.send_command({'verb': 'feeder_process', 'N': N})
        print('feeder process done')

        # hand over
        await rail.set_valves([1, 0])
        await asyncio.sleep(.6)
        await feeder.set_valves([None, 0])
        await rail.set_valves([1, 1])
        await asyncio.sleep(.6)

        # await rail.G1(z=25 * N + 1, feed=6000)
        await rail.send_command_raw('G1 Z%d F1000' % (25 * N + 1))

        await rail.set_valves([1, 0])
        await asyncio.sleep(.6)
        await rail.set_valves([0, 0])
        await asyncio.sleep(1)
        print('everything done')

        await asyncio.gather(
            feeder.G1(z=16, feed=6000),  # Holder Downstream
            # await rail.G1(z=2, feed=6000),  # Holder Downstream
            rail.send_command_raw('G1 Z1 F1000')
        )


async def gather_feeder(system, ALL_NODES):
    for node in ALL_NODES:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    return feeder, rail
