from .node import Node, WAIT_METRIC_TIMEOUT_EXCEPTION
import asyncio
import time
import aioconsole

CONVEYOR_SPEED = 5
LIFT_SPEED = 15


DOSING_TIMEOUT = 3
DOSING_TIMEOUT_FACTOR = 2
DOSING_REVERSE_TIME = .33
'''
in1 -> dosing existance gate -> dosing exitsts -> red light on -> read value = 1

'''


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
        ('sr', {'uda0': True, 'stat': True}),
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
            'conveyor_direction': 7,
        },
        'eac': [],
    }

    def __init__(self, *args, **kwargs):
        self.feeding_task = None
        self.motor_control_task = None
        self.buffer_full_time = None
        super().__init__(*args, **kwargs)

    async def home_core(self):
        pass

    async def create_feeding_loop(self, feeder, recipe):
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
            self.feeding_loop(feeder, recipe))
        self.motor_control_task = asyncio.create_task(
            self.motor_control_loop(feeder, recipe))

    async def terminate_feeding_loop(self, feeder):
        if self.feeding_task is None:
            return

        async with self.shield:
            self.feeding_task.cancel()
            self.motor_control_task.cancel()

            # system to normal conditions
            await self.set_valves([0] + [None] * 5 + [0])
            await self.set_motors_highlevel(feeder, 'off')

        self.motor_control_task = None
        self.feeding_task = None

    async def feeding_loop(self, feeder, recipe):
        while True:
            await self.set_valves([0])

            # wait for optic sensor input=1
            timeout = DOSING_TIMEOUT
            while True:
                try:
                    await self.wait_metric('in1', timeout=timeout)
                    break
                except WAIT_METRIC_TIMEOUT_EXCEPTION as e:
                    # run motor in reverse
                    await self.run_motor_in_reverse(reverse_time=DOSING_REVERSE_TIME)
                    timeout = DOSING_TIMEOUT * DOSING_TIMEOUT_FACTOR

            # detect direction
            direction = await self.detect_direction()
            await self.set_valves([None, direction])

            # wait for buffer to be free
            self.buffer_full_time = time.time()
            self.buffer_empty_event.clear()
            await self.wait_metric('in3', 0)
            self.buffer_full_time = None
            self.buffer_empty_event.set()
            asyncio.create_task(self.plus_plus(feeder))
            # wait for jacks to be stable
            await asyncio.sleep(.05)

            # this two lines must be shielded from cancelation
            async with self.shield:
                await self.set_valves([1])
                await asyncio.sleep(.4)

    async def plus_plus(self, feeder):
        # await asyncio.sleep(.5)
        await feeder.send_command({'verb': 'set_dosing_reserve', 'change': 1})

    async def motor_control_loop(self, feeder, recipe):
        motors_on = True
        await self.set_motors_highlevel(feeder, 'on')
        while True:
            if motors_on:
                await asyncio.sleep(1)
                buffer_full_time = self.buffer_full_time
                if buffer_full_time is None:
                    continue
                buffer_full_time = time.time() - buffer_full_time
                if (buffer_full_time > 1):
                    asyncio.create_task(feeder.send_command(
                        {'verb': 'set_dosing_reserve', 'value': 8}))

                if (buffer_full_time > 30):
                    motors_on = False
                    await self.set_motors_highlevel(feeder, 'standby')
            else:  # motors off
                await self.buffer_empty_event.wait()
                await self.set_motors_highlevel(feeder, 'resume')
                motors_on = True

    async def set_motors_highlevel(self, feeder, status):
        if status == 'on':
            await asyncio.shield(self.set_motors(feeder, (5, LIFT_SPEED), (9, CONVEYOR_SPEED)))
        elif status == 'off':
            await asyncio.shield(self.set_motors(feeder, (5, 0), (9, 0)))
        elif status == 'standby':
            await asyncio.shield(self.set_motors(feeder, (9, 0)))
        elif status == 'resume':
            await asyncio.shield(self.set_motors(feeder, (9, CONVEYOR_SPEED)))

    async def set_motors(self, feeder, *args):
        direct_motors = {9}
        args_direct = [(i, j) for i, j in args if i in direct_motors]
        args_proxy = [(i, j) for i, j in args if i not in direct_motors]

        await self.set_motors_direct(*args_direct)
        if args_proxy:  # needed because we may pass feeder as None
            await feeder.set_motors(*args_proxy)

    async def set_motors_direct(self, *args):
        if len(args) == 0:
            return
        # command = ','.join(
        #     ['m%d:%d' % (i, j) for i, j in args])
        # command = '{%s}' % command
        command = '{m1:%d}' % args[0][1]  # only M1 enabled
        await self.send_command_raw(command)

    async def run_motor_in_reverse(self, reverse_time):
        await self.set_motors(None, (9, 0))
        await self.set_valves([None] * 6 + [1])
        await asyncio.sleep(.1)
        # feeder not available
        await self.set_motors(None, (9, CONVEYOR_SPEED))

        await asyncio.sleep(reverse_time)

        await self.set_motors(None, (9, 0))
        await self.set_valves([None] * 6 + [0])
        await asyncio.sleep(.1)
        await self.set_motors(None, (9, CONVEYOR_SPEED))

    async def detect_direction(self):
        T_FIRST_READ = .030  # wait for proximity_input value established
        T_INTER_READ = .006
        N_READ_COUNT = 30
        P_THRESHOLD = 0.25
        # wait for proximity_input value established
        await asyncio.sleep(T_FIRST_READ)
        i = 0
        while True:

            confidence, proximity_input = await self.read_proximity(n=N_READ_COUNT, delay=T_INTER_READ, threshold=P_THRESHOLD)

            if (confidence > .6):
                break

            if (i > 2):
                proximity_input = 0
                break

            i += 1

            await asyncio.sleep(.15)

        return proximity_input

    async def read_proximity(self, n, delay, threshold):
        read_out = []
        for i in range(n):
            proximity_input = await self.read_metric('in2')
            read_out.append(proximity_input)
            await asyncio.sleep(delay)

        mean = sum(read_out) / float(n)
        value = int(mean > threshold)
        confidence = (mean - threshold) / (value - threshold)

        return confidence, value
