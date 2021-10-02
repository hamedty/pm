import time
import asyncio
from .main import *
import traceback
import aioconsole
from .recipe import *
from scripts import recipe


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)

    # stations = stations[4:]
    # H_ALIGNING H_PUSH H_PRE_DANCE
    # for station in stations:
    #     await station.G1(z=station.hw_config['H_ALIGNING'], feed=5000)
    #     await asyncio.sleep(1)

    # v = 0
    # while True:
    #     v = 1 - v
    #     await asyncio.gather(*[station.set_valves([0, 0, v]) for station in stations])
    #     await asyncio.sleep(2)

    # # await feeder.home()
    # t0 = time.time()
    # z = 16
    # feed = 50000
    # # for i in range(10):
    # #     z += 25
    # #     await feeder.G1(z=z, feed=feed)
    # command = ''
    # for i in range(10):
    #     z += 25
    #     command += 'G1Z%dF%d\n' % (z, feed)
    #
    # await feeder.send_command_raw(command)
    #
    # print(time.time() - t0)

    for i in range(50):
        await asyncio.gather(*[s.set_valves([0] * 4 + [i % 2]) for s in stations[2:3]])

        await asyncio.sleep(0.8)
