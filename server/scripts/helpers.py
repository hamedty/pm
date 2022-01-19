import time
import asyncio
from .main import *
from .recipe import *
from scripts import recipe
import aioconsole


async def fill_cartridge_conveyor(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)
    await feeder.set_motors(
        (6, 300),  # Cartridge Conveyor
        (8, 20),  # Cartridge Conveyor
    )


async def fill_dosing_rail(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)
    await dosing_feeder.create_feeding_loop(feeder, recipe)
    await asyncio.sleep(20)
    await dosing_feeder.terminate_feeding_loop(feeder)


async def run_rail_empty(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    await check_home_all_nodes(system, all_nodes, feeder, rail, robots, stations)
    await rail.set_valves([0, 0])
    await feeder.set_valves([0] * 14)

    await system.system_running.wait()

    while system.system_running.is_set():
        await rail.set_valves([0] * 2)
        await system.system_running.wait()
        await rail.G1(z=recipe.D_MIN, feed=recipe.FEED_RAIL_FREE)
        await rail.set_valves([1, 0])
        await asyncio.sleep(recipe.T_RAIL_JACK1)
        await rail.set_valves([1, 1])
        await asyncio.sleep(recipe.T_RAIL_JACK2)

        # rail forward
        await rail.G1(z=recipe.D_STANDBY, feed=recipe.FEED_RAIL_INTACT)

        # change jacks to moving
        await rail.set_valves([1, 0])
        await asyncio.sleep(recipe.T_RAIL_JACK1)
        await rail.set_valves([0, 0])
        await asyncio.sleep(recipe.T_RAIL_JACK2)


async def pickup_rail(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    await check_home_all_nodes(system, all_nodes, feeder, rail, robots, stations)

    robot = robots[1]
    Y_GRAB_IN_UP_1 = 75
    X_GRAB_IN = 284.5
    Y_GRAB_IN_DOWN = 0
    Y_GRAB_IN_UP_2 = 65
    T_GRAB_IN = 0.5

    await robot.G1(y=Y_GRAB_IN_UP_1, feed=recipe.FEED_Y_UP)
    await robot.G1(x=X_GRAB_IN, feed=recipe.FEED_X)
    await robot.G1(y=Y_GRAB_IN_DOWN, feed=recipe.FEED_Y_DOWN)
    await robot.set_valves_grab_infeed()
    await asyncio.sleep(T_GRAB_IN)
    await robot.G1(y=Y_GRAB_IN_UP_2, feed=recipe.FEED_Y_UP)

    X_INPUT = 373
    Y_INPUT_DOWN_RELEASE_HOLDER = 36
    Y_INPUT_DOWN_RELEASE_DOSING = 32
    Y_INPUT_UP = 55
    Y_INPUT_DOWN_PRESS_HOLDER = 6
    Y_INPUT_DOWN_PRE_PRESS_HOLDER = Y_INPUT_DOWN_PRESS_HOLDER + 10
    Y_OUTPUT = 80
    X_OUTPUT_SAFE = self.hw_config['X_CAPPING']

    Z_OUTPUT = 70
    Z_OUTPUT_SAFE = Z_OUTPUT - 20

    T_INPUT_RELEASE = 1.1
    T_HOLDER_JACK_CLOSE = 0.1
    T_PRE_PRESS = 0.05
    T_POST_PRESS = 0.1
    T_OUTPUT_GRIPP = 0.1
    T_OUTPUT_RELEASE = 0.2

    await robot.G1(x=X_INPUT - .5, feed=recipe.FEED_X)

    await robot.G1(y=50, feed=recipe.FEED_Y_DOWN)
    await aioconsole.ainput('continue?')

    await robot.G1(y=Y_INPUT_DOWN_RELEASE_HOLDER, feed=recipe.FEED_Y_DOWN)
    await robot.set_valves([None] * 5 + [0] * 5)
    await robot.G1(y=Y_INPUT_DOWN_RELEASE_DOSING, feed=recipe.FEED_Y_DOWN)
    await robot.set_valves([0] * 10)
    await asyncio.sleep(T_INPUT_RELEASE)
    await robot.G1(y=Y_INPUT_UP, feed=recipe.FEED_Y_UP)
    await robot.set_valves([0] * 5 + [1] * 5)
    await asyncio.sleep(T_HOLDER_JACK_CLOSE)
    await robot.G1(y=Y_INPUT_DOWN_PRE_PRESS_HOLDER, feed=recipe.FEED_Y_DOWN)
    await asyncio.sleep(T_PRE_PRESS)
    await robot.G1(y=Y_INPUT_DOWN_PRESS_HOLDER, feed=recipe.FEED_Y_DOWN_PRESS)
    await asyncio.sleep(T_POST_PRESS)
    await robot.set_valves([0] * 10)
    await robot.G1(y=Y_OUTPUT, feed=recipe.FEED_Y_UP)


async def holder_feeder_forever(system, ALL_NODES):
    await system.system_running.wait()
    while system.system_running.is_set():
        await holder_feeder(system, ALL_NODES)
        await feeder_handover_to_rail(system, ALL_NODES)


async def holder_feeder(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    # rail, feeder homed and parked
    assert await rail.is_homed(), 'Rail is not homed!'
    assert await feeder.is_homed(), 'Feeder is not homed!'
    assert rail.is_at_loc(z=D_STANDBY), 'rail is in bad location'

    # jack's to normal
    await rail.set_valves([0, 0])
    valves = [0] * 14
    valves[9] = 1
    await feeder.set_valves(valves)

    # G1 Z16
    await feeder.G1(z=FEEDER_Z_IDLE, feed=FEED_FEEDER_COMEBACK)

    # Motors on
    await feeder.set_motors(
        (2, 4), (3, 4),  # Holder Downstream
        # (4, 4), (7, 11),  # Holder Upstream - Lift and long conveyor
        (1, 3750), (10, 35000),  # holder gate on/off
        (6, 20),  (8, 10)  # Cartridge Conveyor + Randomizer
    )
    await feeder.set_valves([None] * 9 + [1])

    holder_mask = [1] * recipe.N
    dosing_mask = [int(not recipe.SERVICE_FUNC_NO_DOSING)] * recipe.N
    cartridge_feed = 0 if recipe.SERVICE_FUNC_NO_CARTRIDGE else 1
    command = {
        'verb': 'feeder_process',
        'holder_mask': holder_mask,
        'dosing_mask': dosing_mask,
        'cartridge_feed': cartridge_feed,
        'z_offset': recipe.FEEDER_Z_IDLE,
        'feed_feed': recipe.FEED_FEEDER_FEED,
        'jerk_feed': recipe.JERK_FEEDER_FEED,
        'jerk_idle': recipe.JERK_FEEDER_DELIVER,
    }
    await feeder.send_command(command)

    # G1 Z717
    await feeder.G1(z=recipe.FEEDER_Z_DELIVER, feed=recipe.FEED_FEEDER_DELIVER)


async def feeder_handover_to_rail(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    # rail, feeder homed and parked
    assert await rail.is_homed(), 'Rail is not homed!'
    assert await feeder.is_homed(), 'Feeder is not homed!'
    assert rail.is_at_loc(z=D_STANDBY) or rail.is_at_loc(
        z=D_MIN), 'rail is in bad location'
    # assert feeder.is_at_loc(z=FEEDER_Z_DELIVER) or feeder.is_at_loc(
    #     z=FEEDER_Z_IDLE), 'feeder is in bad location'

    # jack's to normal
    await rail.set_valves([0, 0])

    await feeder.G1(z=FEEDER_Z_DELIVER, feed=5000), 'feeder is in bad location'
    await rail.G1(z=recipe.D_MIN, feed=recipe.FEED_RAIL_FREE)
    await rail.set_valves([1, 0])
    await asyncio.sleep(recipe.T_RAIL_FEEDER_JACK)
    await feeder.set_valves([None, 0])
    await asyncio.sleep(recipe.T_RAIL_JACK1 - recipe.T_RAIL_FEEDER_JACK)
    await rail.set_valves([1, 1])
    await asyncio.sleep(recipe.T_RAIL_JACK2)
    await rail.G1(z=recipe.D_STANDBY, feed=recipe.FEED_RAIL_INTACT)
    await rail.set_valves([1, 0])
    await asyncio.sleep(recipe.T_RAIL_JACK1)
    await rail.set_valves([0, 0])
    await asyncio.sleep(recipe.T_RAIL_JACK2)


async def motors_off(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)
    await feeder.set_motors()
    valves = [0] * 14
    valves[1] = None  # comb
    await feeder.set_valves(valves)


async def motors_on(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)
    await feeder.set_motors(
        (2, 4), (3, 4),  # Holder Downstream
        # Holder Upstream - Lift and long conveyor
        (4, 4), (7, 11),
        (1, 3750), (10, 35000),  # holder gate on/off
        (6, 25),  (8, 8)  # Cartridge Conveyor + Randomizer
    )
    await dosing_feeder.set_motors_highlevel(feeder, 'on')
