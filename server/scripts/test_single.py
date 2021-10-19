import time
from .main import *
import asyncio
import traceback
import aioconsole
from .recipe import *
from scripts import recipe
from node import ALL_NODES_DICT


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)

    dosing_feeder = ALL_NODES_DICT['Dosing F. 1']
    holder_feeder = ALL_NODES_DICT['Feeder 1']

    # await holder_feeder.send_command_raw('{out11:1}')

    t1 = asyncio.create_task(
        dosing_feeder.feeding_loop(holder_feeder, system, recipe))

    try:
        await asyncio.sleep(100000)
    except:
        pass

    system.system_stop.set()
    await asyncio.sleep(1)
    t1.cancel()
    await self.set_valves([0, None, 0])
    await feeder.set_motors((5, 0), (9, 0))
