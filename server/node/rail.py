import asyncio
from .robot import Robot


class Rail(Robot):
    type = 'rail'
    arduino_reset_pin = 2
    HOMMING_RETRIES = 10

    g2core_config_base = [
        (1, {
            'ma': 2,  # map to Z
            'sa': 1.8,  # step angle 1.8
            'tr': 25,  # travel per rev = 5mm
            'mi': 2,  # microstep = 2
            'po': 1,  # direction
        }),
        ('z', {
            'am': 1,  # standard axis mode
            'vm': 50000,  # max speed
            'fr': 50000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 496,  # max travel -- 496
            'jm': 2000,  # max jerk
            'jh': 10000,  # hominzg jerk
            'hi': 2,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 500,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di2mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di2ac', 0),
        ('di2fn', 0),
        ('gpa', 2),  # equivalent of G64
        ('sv', 2),  # Status report enabled
        ('sr', {'line': True, 'posz': True, 'stat': True}),
        ('si', 250),  # also every 250ms
    ]

    hw_config_base = {
        'valves': {
            'reserve1': 1,
            'reserve2': 2,
            'reserve3': 3,
            'reserve4': 4,
            'reserve5': 5,
            'reserve6': 6,
            'reserve7': 7,
            'reserve8': 8,
            'moving': 9,
            'fixed': 10,
        },
        'di': {
            'z-': 1,
        },
        'encoders': {
            'posz': ['enc1', 64.0, 1],  # encoder key, ratio, telorance
        }

    }

    async def set_valves(self, values):
        values = [0] * 8 + values
        return await super(Rail, self).set_valves(values)

    async def home_core(self):
        await self.send_command_raw('G28.2 Z0')

        # reset encoder
        await self.send_command_raw('G28.5')
        await self.send_command_raw('G1 Z1 F1000')
        await self.send_command_raw('G1 Z0 F1000')
        await asyncio.sleep(1)

    def init_events(self):
        self.rail_move_event = asyncio.Event()  # setter: robot - waiter: rail
        self.rail_move_event.clear()
        self.events['rail_move_event'] = self.rail_move_event

        assert abs(self._status['r.posz'] - 250) < 1, 'Rail must be parked'
        self.rail_parked_event = asyncio.Event()  # setter: rail - waiter: robot
        self.rail_parked_event.clear()
        self.events['rail_parked_event'] = self.rail_parked_event

    async def rail_loop(self, system, recipe, feeder):
        assert abs(self._status['r.posz'] - 250) < 1, 'Rail must be parked'
        self.rail_parked_event.set()
        feeder.feeder_rail_is_parked_event.set()

        while not self.system_stop.is_set():
            await self.rail_move_event.wait()
            self.rail_move_event.clear()

            # rail backward
            await system.system_running.wait()
            await self.G1(z=recipe.D_MIN, feed=recipe.FEED_RAIL_FREE)

            # wait for feeder
            await feeder.feeder_is_full_event.wait()
            feeder.feeder_is_full_event.clear()

            # change jacks to moving
            await system.system_running.wait()
            await self.set_valves([1, 0])
            await asyncio.sleep(recipe.T_RAIL_JACK1 * recipe.T_RAIL_FEEDER_JACK_PERCENTAGE)
            await feeder.set_valves([None, 0])
            await asyncio.sleep(recipe.T_RAIL_JACK1 * (1 - recipe.T_RAIL_FEEDER_JACK_PERCENTAGE))
            await self.set_valves([1, 1])
            await asyncio.sleep(recipe.T_RAIL_JACK2)

            # rail forward
            await system.system_running.wait()
            await self.G1(z=recipe.D_STANDBY, feed=recipe.FEED_RAIL_INTACT)

            # clear feeder
            feeder.feeder_is_empty_event.set()
            self.rail_parked_event.set()

            # change jacks to moving
            await self.set_valves([1, 0])
            await asyncio.sleep(recipe.T_RAIL_JACK1)
            await self.set_valves([0, 0])
            await asyncio.sleep(recipe.T_RAIL_JACK2)

            feeder.feeder_rail_is_parked_event.set()
