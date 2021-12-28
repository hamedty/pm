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
    r = robots[1]
    # await r.home()
    # await r.send_command_raw("{enc1: 1}")
    # await asyncio.sleep(.1)
    await r.send_command_raw('{jt: 5}')
    await r.send_command_raw('{ct: 0.2}')

    await asyncio.sleep(.1)

    t0 = time.time()
    # await r.send_command_raw('''
    # G1 Y30 F55000
    # G2 X30 Y60 I30 J0 F55000
    # G1 X100 F35000
    # ''')
    await r.send_command_raw('''
    G1 Y60 F55000
    G1 X100 F35000
    ''')
    print('---------------------------', time.time() - t0)
    await r.send_command_raw('''
    G4 P.5

    G1X0Y0F10000
    ''')
