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

    mask = [1] * recipe.N
    mask[5] = 0  # station 3
    print('-------------------')
    command = {
        'verb': 'feeder_process',
        'mask': mask,
        'cartridge_feed': not recipe.SERVICE_FUNC_NO_CARTRIDGE,
        'z_offset': recipe.FEEDER_Z_IDLE,
        'feed_comeback': recipe.FEED_FEEDER_COMEBACK,
        'feed_feed': recipe.FEED_FEEDER_FEED,
        'jerk_feed': recipe.JERK_FEEDER_FEED,
        'jerk_idle': recipe.JERK_FEEDER_DELIVER,
    }
    a = await feeder.send_command(command)
    print(a)
