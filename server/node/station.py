import time
from .node import Node
import os
import json
import asyncio


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
        # ('out', {7: 1, 8: 1, 9: 1}),  # Microstepping enabled - done in FW

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
        # ('out', {10: 1, 11: 1, 12: 1}),  # Microstepping enabled -  - done in FW

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
            'lb': 3,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di1mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di4mo', 1),  # Homing Switch for Some - Mode = Active High - NC
        ('sv', 2),  # Status report enabled
        ('sr', {'uda0': True, 'posz': True, 'stat': True}),
        ('si', 250),  # also every 250ms
    ]

    hw_config_base = {
        'valves': {
            'dosing': 1,
            'holder': 2,
            'main': 3,
            'dosing_base': 4,
            'gate': 5,
            'light_red': 6,
            'light_green': 7,
            'motor_enable1': 8,
            'motor_enable2': 9,
        },
        'di': {
            'jack': 1,  # jack verification
            'gate': 2,  # gate verification
        },
        'encoders': {
            # encoder key, ratio, telorance_soft, telorance_hard
            'posz': ['enc1', 300.0, .7, 5.0],
        },
        'eac': [500 * 2],
        'H_ALIGNING': 210,
        'H_PUSH': 219,
        'H_PRE_DANCE': 224,
        'H_DELIVER': -1,
        'holder_offset': 0,
        'dosing_offset': 0,
        'holder_webcam_direction': 'up',
        'dosing_webcam_direction': 'liu',  # liu: Left Is Up - riu: Right Is Up
        'presence_threshold': {'holder': 80, 'dosing': 50},
        'holder_existance_y_margin': 30,
        'dosing_sit_right': {
            'brightness_threshold': 25,
            'existance_count_threshold': 250,
            'wrong_sitting_count_threshold': 20,
        },
        'cameras': {'holder': {'rois': {}}, 'dosing': {'rois': {}}},
    }

    async def home_core(self):
        await self.send_command_raw('G28.2 Z0')

        # reset encoder
        await self.send_command_raw('G28.5')
        await self.send_command_raw('G1 Z1 F1000')
        await self.send_command_raw('G1 Z0 F1000')
        await self.send_command_raw('{out4:1}')

    def calc_rois(self):
        annotation_data = VISION_ANNOTATION[str(self.ip_short)]

        # Holder
        roi_holder = annotation_data['holder_roi']

        # ROI holder presence
        x_margin = 20
        y_margin = self.hw_config['holder_existance_y_margin']
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

        # ROI Dosing Alignment
        DOSING_Y_MARGIN = 30
        roi_dosing_alignment = dict(roi_dosing)
        roi_dosing_alignment['y0'] -= DOSING_Y_MARGIN
        roi_dosing_alignment['dy'] += 2 * DOSING_Y_MARGIN

        # ROI Dosing Sit Right
        y_margin = 40
        direction = self.hw_config['dosing_webcam_direction']

        y0 = int(roi_dosing['y0'] + (roi_dosing['dy'] / 2) - y_margin / 2)
        dy = y_margin
        dx = 450
        x0 = (640 - dx - 40) if direction == 'liu' else 40
        roi_dosing_sit_right = {'x0': x0, 'dx': dx, 'y0': y0, 'dy': dy}

        dosing_roi = {
            'alignment': roi_dosing_alignment,
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

    async def station_assembly_loop(self):
        while True:
            self.update_recipe()
            await self.set_valves([None, 0, 0, 1])
            await self.station_is_full_event.wait()
            self.station_is_full_event.clear()

            check_fullness = await self.send_command({'verb': 'detect_vision', 'object': 'no_holder_no_dosing'})
            check_fullness = check_fullness[1]
            full = check_fullness['dosing_present'] and check_fullness['holder_present']
            empty = check_fullness['no_holder_no_dosing']

            await self.system.system_running.wait()
            if full:
                await self.align_holder()
            await self.station_is_safe_event.wait()
            self.station_is_safe_event.clear()
            if full:
                await self.align_dosing()
                await self.assemble()
                self.system.stats.add_success()

            if not (full or empty):
                # {"no_dosing":false,"no_holder":true,}
                if check_fullness['no_dosing']:  # no dosing
                    message = 'دوزینگ وجود ندارد. استیشن را خالی کنید.'
                else:  # no holder
                    message = 'هولدر وجود ندارد. استیشن را خالی کنید.'

                error = {
                    'message': message,
                    'location_name': self.name,
                    'details': check_fullness,
                    'type': 'error',
                }
                print(error)
                error_clear_event, error_id = await self.system.register_error(error)
                await error_clear_event.wait()
            self.station_is_done_event.set()

    async def clearance(self):
        await self.station_is_done_event.wait()
        self.station_is_done_event.clear()
        await self.verify_no_holder_no_dosing()
        print(f'station {self.name} cleared!')

    async def align_holder(self):
        await self.set_valves([0, 1])
        z1, z2 = await self.send_command({'verb': 'align', 'component': 'holder', 'speed': self.recipe.ALIGN_SPEED_HOLDER, 'retries': self.recipe.VISION_RETRIES_HOLDER}, assert_success=False)
        # print(self.name, z1, z2)
        if (not z1) or (not z2['aligned']):
            error = {
                'message': 'هولدر را دستی تنظیم کنید.',
                'location_name': self.name,
                'details': (z1, z2),
                'type': 'error',
            }
            print(error)
            # await aioconsole.ainput(str(error))
            error_clear_event, error_id = await self.system.register_error(error)
            await error_clear_event.wait()
        if 'steps_history' in z2:
            data = {
                'station': self.ip_short,
                'component': 'holder',
                'steps': z2['steps_history'],
            }
            table = 'vision_retries'
            self.system.mongo.write(table, data)

    async def align_dosing(self):
        data = {}
        data['H_ALIGNING'] = self.hw_config['H_ALIGNING']
        data['FEED_ALIGNING'] = self.recipe.FEED_Z_DOWN
        await self.G1(z=data['H_ALIGNING'], feed=data['FEED_ALIGNING'], correct_initial=True)
        await self.set_valves([1])
        z1, z2 = await self.send_command({'verb': 'align', 'component': 'dosing', 'speed': self.recipe.ALIGN_SPEED_DOSING, 'retries': self.recipe.VISION_RETRIES_DOSING}, assert_success=False)
        if (not z1) or (not z2['aligned']):
            await self.set_valves([0, None, None, None])
            await self.G1(z=100, feed=5000)
            error = {
                'message': 'دوزینگ را دستی تنظیم کنید.',
                'location_name': self.name,
                'details': (z1, z2),
                'type': 'error',
            }
            print(error)
            # await aioconsole.ainput(str(error))
            error_clear_event, error_id = await self.system.register_error(error)
            await error_clear_event.wait()
        if 'steps_history' in z2:
            data = {
                'station': self.ip_short,
                'component': 'dosing',
                'steps': z2['steps_history'],
            }
            table = 'vision_retries'
            self.system.mongo.write(table, data)

    async def verify_no_holder_no_dosing(self):
        while True:
            res = await self.send_command({'verb': 'detect_vision', 'object': 'no_holder_no_dosing'})
            if res[1]['no_holder_no_dosing']:
                break

            await self.set_valves([None] * 3 + [0])
            error = {
                'message': 'استیشن باید خالی باشد. خالی نیست!',
                'location_name': self.name,
                'details': res,
                'type': 'error',
            }
            print(error)
            error_clear_event, error_id = await self.system.register_error(error)
            await error_clear_event.wait()
        await self.set_valves([None] * 3 + [1])

    async def verify_dosing_sit_right_and_come_down(self):
        res = await self.send_command({'verb': 'detect_vision', 'object': 'dosing_sit_right'})
        if not res[1]['sit_right']:
            error = {
                'message': 'دوزینگ بد وارد شده!',
                'location_name': self.name,
                'details': res,
                'type': 'error',
            }
            print(error)
            # await aioconsole.ainput(str(error))
            error_clear_event, error_id = await self.system.register_error(error)
            await error_clear_event.wait()
        await self.G1(z=self.recipe.STATION_Z_OUTPUT, feed=self.recipe.FEED_Z_DOWN)

    async def assemble(self):
        # Dance
        dance_rev = .5
        charge_h = 0.1
        H_DANCE = self.hw_config['H_PRE_DANCE'] - (11 * dance_rev + charge_h)
        Y_DANCE = 360 * dance_rev

        # Dance Back
        H_DANCE_BACK = H_DANCE + charge_h
        H_DANCE_BACK2 = self.hw_config['H_PRE_DANCE']
        Y_DANCE_BACK = 0
        Y_DANCE_BACK2 = -7

        await self.send_command_raw(f'''
            ; release dosing
            M100 ({{out4: 0}})
            G4 P.2
            G1 Z{self.hw_config['H_PRE_DANCE'] - 1:.1f} F5000
            G4 P.07
            M100 ({{out4: 1}})
            G4 P.1
            M100 ({{out1: 0}})
            G4 P.1
            M100 ({{out4: 0}})


            ; ready to push
            G1 Z{self.hw_config['H_ALIGNING'] - 18:.1f} F{int(self.recipe.FEED_Z_UP):d}
            M100 ({{out1: 1}})
            G4 P.05

            ; push and come back
            G1 Z{self.hw_config['H_PUSH']:.1f} F{int(self.recipe.FEED_Z_DOWN / 3.0):d}
            G4 P.1
            G1 Z{self.hw_config['H_PUSH'] - 5:.1f} F{int(self.recipe.FEED_Z_UP):d}

            ; prepare for dance
            G10 L20 P1 Y0
            M100 ({{zjm:5000}})

            M100 ({{out1: 0, out4: 1}})
            G1 Z{self.hw_config['H_PRE_DANCE']:.1f} F{int(self.recipe.FEED_Z_UP * .7):d}
            G4 P.05
            M100 ({{out1: 1, out8: 1}})
            G4 P.05

            ; dance
            G1 Z{H_DANCE:.2f} Y{Y_DANCE:.2f} F{int(self.recipe.FEED_DANCE):d}

            ; press
            M100 ({{out1: 0, out2: 0, out4: 0}})
            M100 ({{out5: 1}})
            M100 ({{out3: 1}})
            M100 ({{out8: 0}})
            G4 P1.2
            M100 ({{out3: 0}})

            ; dance back
            M100 ({{out1: 1, out8: 1}})
            G4 P.15
            G1 Z{H_DANCE_BACK:.2f} F5000
            G4 P.15
            M100 ({{ out4: 1, out5: 0}})
            G1 Z{H_DANCE_BACK2:.2f} Y{Y_DANCE_BACK:.2f} F{int(self.recipe.FEED_DANCE):d}
            G1 Y{Y_DANCE_BACK2:.2f} F{int(self.recipe.FEED_DANCE):d}
            M100 ({{out4: 0, out8: 0}})
            M100 ({{zjm:15000}})
        ''')

        # Verification
        # H_VERIFICATION = self.hw_config['H_PRE_DANCE'] - 80
        # await self.G1(z=H_VERIFICATION, feed=data['FEED_DELIVER'])
        # # take picture and scp to dump folder
        # await self.send_command({
        #     'verb': 'dump_frame',
        #     'components': ['dosing'],
        # })
        # asyncio.create_task(self.scp_from(
        #     '~/data/dosing.png', './dump/verification/%d_%d.png' % (self.ip_short, time.time())))

        # deliver
        # await self.G1(z=4, feed=self.recipe.FEED_Z_UP)
        # eac = self.hw_config['eac'][0]
        # await self.send_command_raw(f'''
        #     {{eac1: 0}}
        #     G28.2 Z0
        #     G28.5
        #     G1 Z{self.hw_config['H_DELIVER']:.2f} F1000
        #     {{eac1: {eac}}}
        # ''')
        await self.G1(z=self.hw_config['H_DELIVER'], feed=self.recipe.FEED_Z_UP)
        await self.set_valves([None, None, None, 1])
