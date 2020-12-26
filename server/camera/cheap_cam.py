from .base import CameraBase
from cv2 import *

SERAIL_NOS = [
    '200619',
]


class CheapCam(CameraBase):
    FILE_FORMAT = '/dev/v4l/by-id/usb-9726-%s_Integrated_Camera-video-index0'

    def get_frame(self, pre_fetch=4, roi_index=0):
        frame = super().get_frame(pre_fetch)
        y0, x0 = self.settings['x0y0'][roi_index]
        dy, dx = self.settings['frame_size'][roi_index]
        frame = frame[y0:y0 + dy, x0:x0 + dx, :]
        return frame


def create_camera(index):
    x0y0 = [
        ((50, 195),),
    ]

    v4l2_base = {
        'brightness': 150,
        'contrast': 48,
        'saturation': 58,
        'hue': 0,
        'gamma': 120,
        'gain': 4,
        'power_line_frequency': 1,
        'sharpness': 2,
        'backlight_compensation': 0,
        'white_balance_temperature_auto': 0,
        'white_balance_temperature': 5250,
        'exposure_auto': 1,
        'exposure_absolute': 1500,
        # 'focus_auto': 0,
        # 'focus_absolute': 30,
    }
    v4l2_config = [
        {'exposure_absolute': 27, 'white_balance_temperature': 5750, },
    ]

    v4l2 = dict(v4l2_base)
    v4l2.update(v4l2_config[index])
    frame_size = ((300, 190),)

    return CheapCam(SERAIL_NOS[index], config={}, settings={'x0y0': x0y0[index], 'frame_size': frame_size}, v4l2_config=v4l2)
