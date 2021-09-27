from .node import Node
import os
import json
import asyncio
import aioconsole

PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_PATH = os.path.dirname(PATH)
BASE_PATH = os.path.dirname(SERVER_PATH)
VISION_ANNOTATION_FILE = os.path.join(BASE_PATH, 'models/annotaion.json')

with open(VISION_ANNOTATION_FILE) as f:
    VISION_ANNOTATION = json.loads(f.read())


class Station(Node):
    type = 'station'
    arduino_reset_pin = 21
    HOMMED_AXES = ['z']

    g2core_config_base = [
        # X - Holder Motor
        (1, {
            'ma': 0,  # map to X
            'sa': 1.8,  # step angle 1.8
            'tr': 360,  # travel per rev = 360 degree
            'mi': 32,  # microstep = 32
            'po': 1,  # direction
        }),
        ('x', {
            'am': 1,  # standard axis mode
            'vm': 360000,  # max speed
            'fr': 360000,  # max feed rate
            'jm': 200000,  # max jerk
            'tn': 0,  # min travel
            'tm': 0,  # max travel
        }),
        ('out', {7: 1, 8: 1, 9: 1}),  # Microstepping enabled

        # Y - Dosing Motor
        (2, {
            'ma': 1,  # map to Y
            'sa': 1.8,  # step angle 1.8
            'tr': 360,  # travel per rev = 360 degree
            'mi': 32,  # microstep = 32
            'po': 1,  # direction
        }),
        ('y', {
            'am': 1,  # standard axis mode
            'vm': 360000,  # max speed
            'fr': 360000,  # max feed rate
            'jm': 200000,  # max jerk
            'tn': 0,  # min travel
            'tm': 0,  # max travel
        }),
        ('out', {10: 1, 11: 1, 12: 1}),  # Microstepping enabled

        # Z - Main Motor
        (3, {
            'ma': 2,  # map to Z
            'sa': 1.8,  # step angle 1.8
            'tr': 8,  # travel per rev = 8mm
            'mi': 2,  # microstep = 2
            'po': 1,  # direction
        }),
        ('z', {
            'am': 1,  # standard axis mode
            'vm': 35000,  # max speed
            'fr': 800000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 250,  # max travel
            'jm': 15000,  # max jerk
            'jh': 20000,  # homing jerk
            'hi': 1,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 200,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di1mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di4mo', 1),  # Homing Switch for Some - Mode = Active High - NC
        ('sv', 2),  # Status report enabled
        ('sr', {'line': True, 'posz': True, 'stat': True}),
        ('si', 250),  # also every 250ms
    ]

    hw_config_base = {
        'valves': {
            'dosing': 1,
            'holder': 2,
            'main': 3,
            'dosing_base': 4,
            'gate': 5,
            'reserve': 6,
        },
        'di': {
            'jack': 1,  # jack verification
            'gate': 2,  # gate verification
        },
        'encoders': {
            # encoder key, ratio, telorance_soft, telorance_hard
            'posz': ['enc1', 300.0, .4, 5.0],
        },
        'H_ALIGNING': 210,
        'H_PUSH': 219,
        'H_PRE_DANCE': 224,
        'dosing_offset': 0,
        'holder_webcam_direction': 'up',
        'dosing_webcam_direction': 'liu',  # liu: Left Is Up - riu: Right Is Up
        'presence_threshold': {'holder': 80, 'dosing': 50},
        'cameras': {'holder': {'rois': {}}, 'dosing': {'rois': {}}},
    }

    async def home_core(self):
        await self.send_command_raw('G28.2 Z0')

        # reset encoder
        await self.send_command_raw('G28.5')
        await self.send_command_raw('G1 Z1 F1000')
        await self.send_command_raw('G1 Z0 F1000')

    def calc_rois(self):
        annotation_data = VISION_ANNOTATION[str(self.ip_short)]

        # Holder
        roi_holder = annotation_data['holder_roi']

        # ROI holder presence
        x_margin = 20
        y_margin = 30
        x0 = roi_holder['x0'] + x_margin
        dx = roi_holder['dx'] - 2 * x_margin
        dy = y_margin
        direction = self.hw_config['holder_webcam_direction']
        y0 = 0 if (direction == 'up') else 480 - y_margin
        roi_holder_presence = {'x0': x0, 'dx': dx, 'y0': y0, 'dy': dy}

        holder_roi = {
            'alignment': roi_holder,
            'existance': roi_holder_presence,
        }
        self.hw_config['cameras']['holder']['rois'] = holder_roi
        # Dosing
        roi_dosing = annotation_data['dosing_roi']
        roi_dosing_presence = roi_dosing

        # ROI Dosing Sit Right
        y_margin = 40
        direction = self.hw_config['dosing_webcam_direction']

        y0 = int(roi_dosing['y0'] + (roi_dosing['dy'] / 2) - y_margin / 2)
        dy = y_margin
        dx = 450
        x0 = (640 - dx - 40) if direction == 'liu' else 40
        roi_dosing_sit_right = {'x0': x0, 'dx': dx, 'y0': y0, 'dy': dy}

        dosing_roi = {
            'alignment': roi_dosing,
            'existance': roi_dosing_presence,
            'sit_right': roi_dosing_sit_right,
        }
        self.hw_config['cameras']['dosing']['rois'] = dosing_roi

    def set_robot(self, robot):
        self._robot = robot

    def draw_debug_dump(self):
        pass

    def init_events(self):
        self.station_is_full_event = asyncio.Event()  # setter: robot - waiter: station
        self.station_is_full_event.clear()
        self.events['station_is_full_event'] = self.station_is_full_event

        self.station_is_safe_event = asyncio.Event()  # setter: robot - waiter: station
        self.station_is_safe_event.clear()
        self.events['station_is_safe_event'] = self.station_is_safe_event

        self.station_is_done_event = asyncio.Event()  # setter: station - waiter: robot
        self.station_is_done_event.set()
        self.events['station_is_done_event'] = self.station_is_done_event

    async def station_assembly_loop(self, recipe, system):
        while True:
            await self.station_is_full_event.wait()
            self.station_is_full_event.clear()

            check_fullness = await self.send_command({'verb': 'detect_vision', 'object': 'no_holder_no_dosing'})
            check_fullness = check_fullness[1]
            full = check_fullness['dosing_present'] and check_fullness['holder_present']
            empty = check_fullness['no_holder_no_dosing']

            await system.system_running.wait()
            if full:
                await self.align_holder(recipe, system)
            await self.station_is_safe_event.wait()
            self.station_is_safe_event.clear()
            if full:
                await system.system_running.wait()
                await self.align_dosing(recipe, system)
                await system.system_running.wait()
                await self.assemble(recipe, system)

            if not (full or empty):
                error = {
                    'message': 'Not all elements are present in the station. Remove all to continue.',
                    'location_name': self.name,
                    'details': check_fullness,
                }
                print(error)
                # await aioconsole.ainput(str(error))
                error_clear_event = await system.register_error(error)
                await error_clear_event.wait()
            self.station_is_done_event.set()

    async def clearance(self, system):
        await self.station_is_done_event.wait()
        self.station_is_done_event.clear()
        await self.verify_no_holder_no_dosing(system)

    async def align_holder(self, recipe, system):
        await self.set_valves([0, 1])
        z1, z2 = await self.send_command({'verb': 'align', 'component': 'holder', 'speed': recipe.ALIGN_SPEED_HOLDER, 'retries': 10}, assert_success=False)
        print(self.name, z1, z2)
        if (not z1) or (not z2['aligned']):
            error = {
                'message': 'Aligining failed for holder. Align to continue',
                'location_name': self.name,
                'details': (z1, z2),
            }
            print(error)
            # await aioconsole.ainput(str(error))
            error_clear_event = await system.register_error(error)
            await error_clear_event.wait()

    async def align_dosing(self, recipe, system):
        data = {}
        data['H_ALIGNING'] = self.hw_config['H_ALIGNING']
        data['FEED_ALIGNING'] = recipe.FEED_Z_DOWN
        await self.G1(z=data['H_ALIGNING'], feed=data['FEED_ALIGNING'], system=system)
        await self.set_valves([1])
        z1, z2 = await self.send_command({'verb': 'align', 'component': 'dosing', 'speed': recipe.ALIGN_SPEED_DOSING, 'retries': 10}, assert_success=False)
        print(self.name, z1, z2)
        if (not z1) or (not z2['aligned']):
            # await self.set_valves([None, None, None, 0])
            error = {
                'message': 'Aligining failed for dosing. Align to continue',
                'location_name': self.name,
                'details': (z1, z2),
            }
            print(error)
            # await aioconsole.ainput(str(error))
            error_clear_event = await system.register_error(error)
            await error_clear_event.wait()

    async def verify_no_holder_no_dosing(self, system):
        res = await self.send_command({'verb': 'detect_vision', 'object': 'no_holder_no_dosing'})
        if not res[1]['no_holder_no_dosing']:
            error = {
                'message': 'no-holder-no-dosing failed',
                'location_name': self.name,
                'details': res,
            }
            print(error)
            # await aioconsole.ainput(str(error))
            error_clear_event = await system.register_error(error)
            await error_clear_event.wait()

    async def verify_dosing_sit_right(self, recipe, system):
        res = await self.send_command({'verb': 'detect_vision', 'object': 'dosing_sit_right'})
        print(res)
        if not res[1]['sit_right']:
            error = {
                'message': 'verify_dosing_sit_right failed',
                'location_name': self.name,
                'details': res,
            }
            print(error)
            # await aioconsole.ainput(str(error))
            error_clear_event = await system.register_error(error)
            await error_clear_event.wait()

    async def assemble(self, recipe, system):
        data = {}
        # go to aliging location
        data['H_ALIGNING'] = self.hw_config['H_ALIGNING']
        data['FEED_ALIGNING'] = recipe.FEED_Z_DOWN

        # Fall
        data['PAUSE_FALL_DOSING'] = 0.05

        # Ready to push
        data['H_READY_TO_PUSH'] = data['H_ALIGNING'] - 8
        data['FEED_READY_TO_PUSH'] = recipe.FEED_Z_UP
        data['PAUSE_READY_TO_PUSH'] = 0.05

        # Push
        data['H_PUSH'] = self.hw_config['H_PUSH']
        data['FEED_PUSH'] = recipe.FEED_Z_DOWN / 3.0
        data['PAUSE_PUSH'] = 0.1
        data['H_PUSH_BACK'] = data['H_PUSH'] - 5
        data['FEED_PUSH_BACK'] = recipe.FEED_Z_UP

        # Dance
        data['PAUSE_JACK_PRE_DANCE_1'] = 0.05
        data['PAUSE_JACK_PRE_DANCE_2'] = 0.05
        data['PAUSE_JACK_PRE_DANCE_3'] = 0.05
        data['H_PRE_DANCE'] = self.hw_config['H_PRE_DANCE']
        data['FEED_PRE_DANCE'] = recipe.FEED_Z_UP

        dance_rev = 1
        charge_h = 0.1
        data['H_DANCE'] = data['H_PRE_DANCE'] - \
            ((11 + charge_h) * dance_rev)
        data['Y_DANCE'] = 360 * dance_rev
        data['FEED_DANCE'] = recipe.FEED_DANCE

        # Press
        data['PAUSE_PRESS'] = 2.0  # 1.5

        # Dance Back
        data['PAUSE_JACK_PRE_DANCE_BACK'] = .2
        data['PAUSE_POST_DANCE_BACK'] = .3

        data['H_DANCE_BACK'] = data['H_DANCE'] + (charge_h * dance_rev)
        data['H_DANCE_BACK2'] = data['H_PRE_DANCE']
        data['Y_DANCE_BACK'] = 0
        data['Y_DANCE_BACK2'] = -4
        data['FEED_DANCE_BACK'] = data['FEED_DANCE']

        # Deliver
        data['H_DELIVER'] = .5
        data['FEED_DELIVER'] = recipe.FEED_Z_UP

        command = '''
            ; release dosing
            M100 ({out1: 0, out4: 0})
            G4 P%(PAUSE_FALL_DOSING).2f

            ; ready to push
            G1 Z%(H_READY_TO_PUSH).2f F%(FEED_READY_TO_PUSH)d
            M100 ({out1: 1})
            G4 P%(PAUSE_READY_TO_PUSH).2f

            ; push and come back
            G1 Z%(H_PUSH).2f F%(FEED_PUSH)d
            G4 P%(PAUSE_PUSH).2f
            G1 Z%(H_PUSH_BACK).2f F%(FEED_PUSH_BACK)d

            ; prepare for dance
            G10 L20 P1 Y0
            M100 ({out1: 0, out4: 1})
            G4 P%(PAUSE_JACK_PRE_DANCE_1).2f
            G1 Z%(H_PRE_DANCE).2f F%(FEED_PRE_DANCE)d
            G4 P%(PAUSE_JACK_PRE_DANCE_2).2f
            M100 ({out1: 1})
            G4 P%(PAUSE_JACK_PRE_DANCE_3).2f

            ; dance
            G1 Z%(H_DANCE).2f Y%(Y_DANCE).2f F%(FEED_DANCE)d

            ; press
            M100 ({out1: 0, out2: 0, out4: 0})
            M100 ({out3: 1})
            M100 ({out5: 1})
            G4 P%(PAUSE_PRESS).2f
            M100 ({out3: 0})

            ; dance back
            M100 ({out1: 1, out4: 1, out5: 0})
            G4 P%(PAUSE_JACK_PRE_DANCE_BACK).2f

            G1 Z%(H_DANCE_BACK).2f F5000
            G1 Z%(H_DANCE_BACK2).2f Y%(Y_DANCE_BACK).2f F%(FEED_DANCE_BACK)d
            G1 Y%(Y_DANCE_BACK2).2f F%(FEED_DANCE_BACK)d
            M100 ({out4: 0})
            G4 P%(PAUSE_POST_DANCE_BACK).2f
        ''' % data
        await self.send_command_raw(command)

        await self.G1(z=data['H_DELIVER'], feed=data['FEED_DELIVER'], system=system)
        await self.set_valves([None, None, None, 1])
