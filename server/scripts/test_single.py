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
    s = stations[0]
    await s.home()
    await s.send_command_raw("{enc1: 1}")
    await asyncio.sleep(.1)
    await s.send_command_raw("G1Z200F30000")
    await s.send_command_raw("G1Z0F10000")
