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

    # await robots[0].G1(y=70, feed=20000)
    # await asyncio.sleep(1)
    # await robots[0].G1(y=10, feed=20000)

    # for s in stations[:2]:
    #     # await s.set_valves([1])
    #     # await asyncio.sleep(.5)
    #     await s.G1(z=s.hw_config['H_PRE_DANCE'], feed=5000)
    s = stations[1]
    await s.send_command_raw('G1Z200F10000')
    await asyncio.sleep(.2)
    await s.send_command_raw('G1Z10F10000')

    # await s.align_dosing(recipe)
    # await s.assemble(recipe)
