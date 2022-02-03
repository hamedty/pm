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

    s = stations[-1]

    await s.set_valves([0, 0, 0, 1])
    await asyncio.sleep(1)

    check_fullness = await s.send_command({'verb': 'detect_vision', 'object': 'no_holder_no_dosing'})
    check_fullness = check_fullness[1]
    full = check_fullness['dosing_present'] and check_fullness['holder_present']
    empty = check_fullness['no_holder_no_dosing']

    await asyncio.gather(
        s.align_holder(recipe),
        s.align_dosing(recipe)
    )
    #
    # if full:
    #     await s.align_holder(recipe)
    # # await s.station_is_safe_event.wait()
    # # s.station_is_safe_event.clear()
    # if full:
    #     await s.align_dosing(recipe)
    t0 = time.time()
    await s.assemble(recipe)
    t1 = time.time()
    print(t1 - t0)

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
        }
        print(error)
        error_clear_event, error_id = await s.system.register_error(error)
        await error_clear_event.wait()

    await asyncio.sleep(1)
    await s.set_valves([0, 0, 0, 1])
