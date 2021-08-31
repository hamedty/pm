import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    print('Nodes Ready')

    station = stations[0]

    ''' home '''
    # await station.home()
    # await station.set_valves([0, 0, 0, 1])

    '''holder'''
    # await station.set_valves([0, 1])
    # z1, z2 = await station.send_command({'verb': 'align', 'component': 'holder', 'speed': ALIGN_SPEED_HOLDER, 'retries': 10})
    # print(z1, z2)

    ''' dosing '''
    await station.G1(z=station.hw_config['H_ALIGNING'], feed=FEED_Z_DOWN)
    await asyncio.sleep(.5)
    await station.set_valves([1])
    await asyncio.sleep(.5)

    z1, z2 = await station.send_command({'verb': 'align', 'component': 'dosing', 'speed': ALIGN_SPEED_DOSING, 'retries': 10})
    print(z1, z2)
    if z2['aligned']:
        await station.set_valves([0])
        await asyncio.sleep(.5)
        await station.G1(z=10, feed=FEED_Z_UP)
