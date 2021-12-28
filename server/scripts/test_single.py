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
    await s.set_eac(eac1=50)
    await s.send_command_raw("G1Z100F30000")
    await s.set_eac(eac1=500)
