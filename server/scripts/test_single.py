import time
from .main import *
import asyncio
import traceback
import aioconsole
from .utils import *
from node import ALL_NODES_DICT


@run_exclusively
async def main(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)

    s = stations[5]  # 106

    await s.send_command_raw('{eac1: 100}')
    await asyncio.sleep(.5)
    await s.send_command_raw('G1Z15F10000')
