import time
import asyncio
from .main import *
import traceback
import aioconsole
from .recipe import *
from scripts import recipe


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    self = robots[0]
    Y_GRAB_IN_UP_1 = 75
    X_GRAB_IN = 284.5
    Y_GRAB_IN_DOWN = 0
    Y_GRAB_IN_UP_2 = 65
    T_GRAB_IN = 0.5

    await self.G1(y=Y_GRAB_IN_UP_1, feed=recipe.FEED_Y_UP)
    await self.G1(x=X_GRAB_IN, feed=recipe.FEED_X)
    await self.G1(y=Y_GRAB_IN_DOWN, feed=recipe.FEED_Y_DOWN)
    await self.set_valves_grab_infeed()
    await asyncio.sleep(T_GRAB_IN)
    await self.G1(y=Y_GRAB_IN_UP_2, feed=recipe.FEED_Y_UP)

    X_INPUT = 373
    Y_INPUT_DOWN_1 = 35
    Y_INPUT_UP = 55
    Y_INPUT_DOWN_3 = 6
    Y_INPUT_DOWN_2 = Y_INPUT_DOWN_3 + 10
    Y_OUTPUT = 80
    X_OUTPUT_SAFE = recipe.X_CAPPING

    FEED_Y_PRESS = 3000

    Z_OUTPUT = 70
    Z_OUTPUT_SAFE = Z_OUTPUT - 20

    T_INPUT_RELEASE = 1.0
    T_HOLDER_JACK_CLOSE = 0.1
    T_PRE_PRESS = 0.05
    T_POST_PRESS = 0.1
    T_OUTPUT_GRIPP = 0.1
    T_OUTPUT_RELEASE = 0.2

    # ensure about stations
    await self.G1(x=X_INPUT, feed=recipe.FEED_X)
    # await self.G1(y=Y_INPUT_DOWN_1, feed=recipe.FEED_Y_DOWN)
    # await self.set_valves([0] * 10)
    # await asyncio.sleep(T_INPUT_RELEASE)
    # await asyncio.gather(*[station.verify_dosing_sit_right(recipe, system) for station in self._stations])
    # stations_task2 = asyncio.gather(
    #     *[station.G1(z=Z_OUTPUT, feed=recipe.FEED_Z_DOWN / 4.0) for station in self._stations])
    #
    # await self.G1(y=Y_INPUT_UP, feed=recipe.FEED_Y_UP)
    # await self.set_valves([0] * 5 + [1] * 5)
    # await asyncio.sleep(T_HOLDER_JACK_CLOSE)
    # await self.G1(y=Y_INPUT_DOWN_2, feed=recipe.FEED_Y_DOWN)
    # await asyncio.sleep(T_PRE_PRESS)
    # await self.G1(y=Y_INPUT_DOWN_3, feed=FEED_Y_PRESS)
    # await asyncio.sleep(T_POST_PRESS)
    # await self.set_valves([0] * 10)
    # await stations_task2
    # await self.G1(y=Y_OUTPUT, feed=recipe.FEED_Y_UP)
    # await self.set_valves([1] * 5)
    # await asyncio.sleep(T_OUTPUT_GRIPP)
    # await asyncio.gather(*[station.set_valves([0, 0, 0, 1]) for station in self._stations])
    #
    # await asyncio.sleep(T_OUTPUT_RELEASE)
    # await asyncio.gather(*[station.G1(z=Z_OUTPUT_SAFE, feed=recipe.FEED_Z_UP) for station in self._stations])
    #
    # for station in self._stations:
    #     station.station_is_full_event.set()
