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
            'posz': ['enc1', 300.0, .4],  # encoder key, ratio, telorance
        },
        'H_ALIGNING': 210,
        'H_PUSH': 219,
        'H_PRE_DANCE': 224,
        'dosing_offset': 0,
        'holder_webcam_direction': 'up',
        'dosing_webcam_direction': 'liu',  # liu: Left Is Up - riu: Right Is Up
    }

    def __init__(self, *args, **kwargs):
        super(Station, self).__init__(*args, **kwargs)
        self.calc_rois()

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

        # Dosing
        roi_dosing = annotation_data['dosing_roi']
        roi_dosing_presence = roi_dosing

        # ROI Dosing Sit Right
        y_margin = 40
        direction = self.hw_config['dosing_webcam_direction']

        y0 = int(roi_dosing['y0'] + (roi_dosing['dy'] / 2) - y_margin / 2)
        dy = y_margin
        dx = 450
        x0 = (640 - dx) if direction == 'liu' else 0
        roi_dosing_sit_right = {'x0': x0, 'dx': dx, 'y0': y0, 'dy': dy}

        dosing_roi = {
            'alignment': roi_dosing,
            'existance': roi_dosing_presence,
            'sit_right': roi_dosing_sit_right,
        }

        self.holder_roi = holder_roi
        self.dosing_roi = dosing_roi

    async def send_command_create_camera(self):
        command = {
            'verb': 'create_camera',
            'dosing_roi': self.dosing_roi,
            'holder_roi': self.holder_roi,
        }
        return await self.send_command(command)

    def set_status(self, **kwargs):
        # if 'data' in kwargs:
        #     data = kwargs['data']
        #     kwargs['data'] = data
        super(Station, self).set_status(**kwargs)

    def set_robot(self, robot):
        self._robot = robot

    def draw_debug_dump(self):
        pass
