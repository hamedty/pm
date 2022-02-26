import asyncio


def run_exclusively(func):
    async def wrapper(system, ALL_NODES):
        lock = system.running_script_lock
        try:
            await asyncio.wait_for(lock.acquire(), timeout=.1)
            system.running_script = func.__name__
            await func(system, ALL_NODES)
        except asyncio.TimeoutError:
            print('Script blocked by exclusive lock')
        finally:
            system.running_script = None
            lock.release()

    return wrapper


async def gather_all_nodes(system, ALL_NODES, wait_for_readiness=True):
    stations = [node for node in ALL_NODES if node.name.startswith('Station ')]
    robots = [node for node in ALL_NODES if node.name.startswith('Robot ')]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]
    dosing_feeder = [
        node for node in ALL_NODES if node.name.startswith('Dosing ')][0]

    all_nodes = stations + robots + [rail, feeder]

    # All Nodes Ready?
    if wait_for_readiness:
        for node in all_nodes:
            while not node.ready_for_command():
                await asyncio.sleep(.01)

    return all_nodes, feeder, dosing_feeder, rail, robots, stations


async def check_home_all_nodes(system, all_nodes, feeder, rail, robots, stations):
    # G2Core Flag
    for node in all_nodes:
        # only checks if home squence has beed ran. location must be checked separately
        is_homed = await node.is_homed()
        assert is_homed, '%s is not homed!' % node.name

    # Feeder
    assert feeder.is_at_loc(
        z=feeder.recipe.FEEDER_Z_IDLE) or feeder.is_at_loc(z=feeder.recipe.FEEDER_Z_DELIVER)
    assert await feeder.read_metric('out2') == 0, "Feeder Jack is out - transfer first"

    # Rail
    assert rail.is_at_loc(z=recipe.D_STANDBY)

    # robots
    for robot in robots:
        condition = robot.is_at_loc(
            x=0, y=0) or robot.is_at_loc(x=robot.recipe.X_PARK, y=robot.recipe.Y_PARK)
        message = '%s is not at proper location' % robot.name
        assert condition, message

    # stations
    for station in stations:
        condition = station.is_at_loc(z=station.hw_config['H_DELIVER']) or station.is_at_loc(
            z=40) or station.is_at_loc(z=0)
        message = '%s is not at proper location' % station.name
        assert condition, message
