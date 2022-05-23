import time
from .main import *
import asyncio
import traceback
from .utils import *
from node import ALL_NODES_DICT


@run_exclusively
async def main(system, ALL_NODES):
    # Wait for station to be ready
    s = ALL_NODES_DICT['Station X']
    while not s.ready_for_command():
        await asyncio.sleep(.01)

    print('Station is Ready!')
    # ''' Jacks '''
    # for j in range(1):
    #     for i in range(101):
    #         await s.set_valves([0] * j + [i % 2])
    #         await asyncio.sleep(.1)

    # ''' Home '''
    # await s.home()

    # ''' Z '''
    # for i in range(5):
    #     await s.G1(z=200, feed=15000)
    #     await asyncio.sleep(.5)
    #     await s.G1(z=10, feed=10000)
    #     await asyncio.sleep(.5)

    # ''' X/Y '''
    # for i in range(3):
    #     await s.send_command_raw('''
    #         ; Holder
    #         M100 ({out9: 1})
    #
    #         G10 L20 P1 X0
    #
    #         G1 X360 F25000
    #         G4 P.1
    #         G1 X0 F25000
    #
    #         M100 ({out9: 0})
    #
    #         ; Dosing
    #         M100 ({out8: 1})
    #
    #         G10 L20 P1 Y0
    #
    #         G1 Y360 F25000
    #         G4 P.1
    #         G1 Y0 F25000
    #
    #         M100 ({out8: 0})
    #
    #
    #     ''')
    #     await asyncio.sleep(.1)
