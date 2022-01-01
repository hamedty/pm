import time
from .main import *
import asyncio
import traceback
import aioconsole
from .recipe import *
from scripts import recipe
from node import ALL_NODES_DICT


async def main(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)

    # # # await s.home()
    # # await rail.set_eac(eac1=1000)
    # #
    # # for i in range(1):
    # #     t0 = time.time()
    # #     await rail.send_command_raw('''
    # #         M100.1 ({z:{jm:4500}})
    # #         G1 Z100 F16000
    # #         G4 P.5
    # #         G1 Z350 F16000
    # #     ''')
    # #     print(f'{time.time() - t0:.1f}')
    # #     await asyncio.sleep(.5)
    # r = robots[0]
    # for i in range(1):
    #     t0 = time.time()
    #     await r.send_command_raw('''
    #         G1 X200 F60000
    #         G4 P.5
    #         G1 X20  F60000
    #     ''')
    #     print(f'{time.time() - t0:.1f}')
    #     await asyncio.sleep(.5)
    for i in range(50):
        value = int(i % 2)
        await robots[0].set_valves([None] * 6 + [value, value])
        await asyncio.sleep(.5)
