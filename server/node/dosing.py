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

    def __init__(self, *args, **kwargs):
        self.feeding_task = None
        self.motor_control_task = None
        self.buffer_full_time = None
        super().__init__(*args, **kwargs)

    async def home_core(self):
        pass

    async def create_feeding_loop(self, feeder, system, recipe):
        '''

        feeding_task
        motor_control_task
        create_feeding_loop() ->
                                feeding_loop()          -> buffer_full_time, buffer_empty_event
                                motor_control_loop()    -< buffer_full_time, buffer_empty_event
                                shield


        terminate_feeding_loop()

        '''
        if recipe.SERVICE_FUNC_NO_FEEDER or recipe.SERVICE_FUNC_NO_DOSING:
            return
        if self.feeding_task is not None:
            return
        # shield is a Lock for time sensetive operation inside the loop. Shield must be
        # created here to be in the same event loop as the loop.
        self.shield = asyncio.Lock()
        self.buffer_empty_event = asyncio.Event()
        self.feeding_task = asyncio.create_task(
            self.feeding_loop(feeder, system, recipe))
        self.motor_control_task = asyncio.create_task(
            self.motor_control_loop(feeder, system, recipe))

    async def terminate_feeding_loop(self):
        if self.feeding_task is None:
            return

        async with self.shield:
            self.feeding_task.cancel()
            self.motor_control_task.cancel()

            # system to normal conditions
            await self.set_valves([0])
            await self.set_motors(feeder, 'off')

        self.motor_control_task = None
        self.feeding_task = None

    async def feeding_loop(self, feeder, system, recipe):
        while not system.system_stop.is_set():
            await self.set_valves([0])

            # wait for optic sensor input=1
            await self.wait_metric('in1')
            # wait for proximity_input value established
            await asyncio.sleep(.030)
            confidence = 0
            while True:
                confidence, proximity_input = await self.read_proximity()
                if confidence > .98:
                    break
                await asyncio.sleep(.15)

            await self.set_valves([None, proximity_input])

            # wait for buffer to be free
            self.buffer_full_time = time.time()
            self.buffer_empty_event.clear()
            await self.wait_metric('in3', 0)
            self.buffer_full_time = None
            self.buffer_empty_event.set()

            # wait for jacks to be stable
            await asyncio.sleep(.05)

            # this two lines must be shielded from cancelation
            async with self.shield:
                await self.set_valves([1])
                await asyncio.sleep(.4)

    async def motor_control_loop(self, feeder, system, recipe):
        motors_on = True
        await self.set_motors(feeder, 'on')
        while True:
            if motors_on:
                await asyncio.sleep(1)
                buffer_full_time = self.buffer_full_time
                if buffer_full_time is None:
                    continue
                buffer_full_time = time.time() - buffer_full_time
                if (buffer_full_time > 2):
                    motors_on = False
                    await self.set_motors(feeder, 'off')
            else:  # motors off
                await self.buffer_empty_event.wait()
                await self.set_motors(feeder, 'on')
                motors_on = True

    async def set_motors(self, feeder, status):
        if status == 'on':
            await asyncio.shield(feeder.set_motors((5, 25), (9, 5)))
        else:
            await asyncio.shield(feeder.set_motors((5, 0), (9, 0)))

    async def read_proximity(self):
        read_out = []
        for i in range(30):
            proximity_input = await self.read_metric('in2')
            read_out.append(proximity_input)
            await asyncio.sleep(.005)
        # print(read_out)
        mean = sum(read_out) / float(len(read_out))
        value = int(mean > 0.5)
        confidence = abs(mean - 0.5) * 2
        return confidence, value
