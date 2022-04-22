import time
from .main import *
import asyncio
import traceback

from .recipe import *
from .utils import *
from scripts import recipe
from node import ALL_NODES_DICT


@run_exclusively
async def main(system, ALL_NODES):
    # Wait for station to be ready
    s = ALL_NODES_DICT['Station X']
    while not s.ready_for_command():
        await asyncio.sleep(.01)

    print('aaaaaaaaaaaaaaa')
    check_fullness = await s.send_command({'verb': 'detect_vision', 'object': 'no_holder_no_dosing'})
    check_fullness = check_fullness[1]
    full = check_fullness['dosing_present'] and check_fullness['holder_present']
    empty = check_fullness['no_holder_no_dosing']

    if full:
        await s.align_holder(recipe)
        await s.align_dosing(recipe)
        await s.assemble(recipe)

    if not (full or empty):
        # {"no_dosing":false,"no_holder":true,}
        if check_fullness['no_dosing']:  # no dosing
            message = 'دوزینگ وجود ندارد. استیشن را خالی کنید.'
        else:  # no holder
            message = 'هولدر وجود ندارد. استیشن را خالی کنید.'

        error = {
            'message': message,
            'location_name': s.name,
            'details': check_fullness,
            'type': 'error',
        }
        print(error)
        #     error_clear_event, error_id = await s.system.register_error(error)
        #     await error_clear_event.wait()
        # s.station_is_done_event.set()


# @run_exclusively
# async def main(system, ALL_NODES):
#     # Wait for station to be ready
#     s = ALL_NODES_DICT['Station X']
#     while not s.ready_for_command():
#         await asyncio.sleep(.01)
#
#     print('Station is Ready!')
#
#     # for j in [0]:
#     #     for i in range(11):
#     #         await s.set_valves([0] * j + [i % 2])
#     #         await asyncio.sleep(.5)
#
#     # ''' Home '''
#     # await s.home()
#     #
#     # ''' Lights '''
#     # for j in [5, 6]:
#     #     for i in range(11):
#     #         await s.set_valves([0] * j + [i % 2])
#     #         await asyncio.sleep(.5)
#
#     # ''' Jacks '''
#     # for j in range(7):
#     #     for i in range(11):
#     #         await s.set_valves([0] * j + [i % 2])
#     #         await asyncio.sleep(.5)
#     #
#     # ''' Z '''
#     # for i in range(5):
#     #     await s.G1(z=200, feed=15000)
#     #     await asyncio.sleep(.5)
#     #     await s.G1(z=10, feed=10000)
#     #     await asyncio.sleep(.5)
#     #
#     # ''' X/Y '''
#     # for i in range(5):
#     #     await s.send_command_raw('''
#     #         M100 ({out8: 1, out9: 1})
#     #
#     #         G10 L20 P1 Y0
#     #         G10 L20 P1 X0
#     #
#     #         G1 X3600 Y3600 F35000
#     #         G4 P.1
#     #         G1 X0 Y0 F35000
#     #
#     #         M100 ({out8: 0, out9: 0})
#     #
#     #     ''')
#     #     await asyncio.sleep(1)
#
#     ''' X/Y '''
#     for i in range(1):
#         await s.send_command_raw('''
#             M100 ({out8: 1, out9: 1})
#
#             G10 L20 P1 Y0
#             G10 L20 P1 X0
#
#             G1 X360 Y360 F35000
#             G4 P.1
#             G1 X0 Y0 F35000
#
#             M100 ({out8: 0, out9: 0})
#
#         ''')
#         await asyncio.sleep(1)
