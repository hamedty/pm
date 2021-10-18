from .node import Node
import asyncio
import time
import aioconsole


class Dosing(Node):
    type = 'dosing'
    arduino_reset_pin = 21

    g2core_config_base = [
        ('di1mo', 0),  # NPN
        ('di1ac', 0),
        ('di1fn', 0),

        ('di2mo', 0),  # NPN
        ('di2ac', 0),
        ('di2fn', 0),

        ('di3mo', 0),  # NPN
        ('di3ac', 0),
        ('di3fn', 0),


        ('sv', 2),  # Status report enabled
        ('sr', {'line': True, 'stat': True}),
        ('si', 250),  # also every 250ms
    ]

    hw_config_base = {
        'valves': {
            'rail dosing': 1,
            'rail holder': 2,
            'gate': 3,
            'sub-gate 2': 4,
            'sub-gate 1': 5,
            'pusher': 6,
        },

    }

    async def home_core(self):
        pass

    async def feeding_loop(self, feeder, system, recipe):
        if recipe.SERVICE_FUNC_NO_FEEDER:
            return

        # start dosing conveyor motor
        await feeder.set_motors((5, 25), (9, 5))

        while not system.system_stop.is_set():
            await self.set_valves([0])

            # wait for optic sensor input=1
            await self.wait_metric('in1')

            # wait for proximity_input value established
            await asyncio.sleep(.030)
            confidence = 0
            while True:
                confidence, proximity_input = await self.read_proximity()
                print(I, 'confidence:', confidence, 'value:', proximity_input)
                if confidence > .98:
                    break
                await asyncio.sleep(.15)

            await self.set_valves([None, proximity_input])

            # wait for buffer to be free
            await self.wait_metric('in3', 0)

            # wait for jacks to be stable
            await asyncio.sleep(.05)
            await self.set_valves([1])
            await asyncio.sleep(.4)

        await self.set_valves([0, None, 0])
        await feeder.set_motors((5, 0), (9, 0))

    async def read_proximity(self):
        read_out = []
        for i in range(20):
            proximity_input = await self.read_metric('in2')
            read_out.append(proximity_input)
            await asyncio.sleep(.003)
        # print(read_out)
        mean = sum(read_out) / float(len(read_out))
        value = int(mean > 0.5)
        confidence = abs(mean - 0.5) * 2
        return confidence, value
