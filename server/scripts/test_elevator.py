import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    feeder, rail = await gather_feeder(system, ALL_NODES)
    print('nodes ready')

    for i in range(1, 10):
        await feeder.send_command_raw('{m%d:0}' % i)  # Holder Downstream
    await feeder.set_valves([0] * 14)
    return
    # await rail.home()
    # await rail.G1(z=50, feed=10000)
    # await rail.send_command_raw('G1 Z50.00 F5000')
    # await feeder.send_command_raw('G1 Y50.00 F50000')
    #
    # command = '''
    #     G38.3 Y-100 F2000
    #     G10 L20 P1 Y0
    #     '''
    # await feeder.send_command_raw(command)

    await feeder.home()
    await feeder.send_command_raw('''M100 ({out9: 1, out13: 1})
                                    G1 Y100 F60000''')
    input('?')
    await feeder.send_command_raw("{out4: 1}")  # push cartridge forward
    input('?')
    await feeder.send_command_raw("{out9: 0}")  # bring jack up
    input('?')
    await feeder.send_command_raw("{out4: 0}")  # pull cartridge pusher back
    input('?')
    await feeder.send_command_raw("G1 Y10 F6000")
    input('?')
    # bring jack up in middle of air
    await feeder.send_command_raw("{out9: 1}")
    input('?')


async def gather_feeder(system, ALL_NODES):
    for node in ALL_NODES:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    return feeder, rail
