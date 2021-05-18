from .base import CameraBase
from cv2 import *

SERAIL_NOS = {
    'holder': '1',
    'dosing': '2',
}

DEFAULT_PRE_FETCH = 4


class CheapCam(CameraBase):
    FILE_FORMAT = '/dev/v4l/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.%s:1.0-video-index0'
    CONFIG_BASE = {
        CAP_PROP_FOURCC: VideoWriter_fourcc('M', 'J', 'P', 'G'),
        CAP_PROP_FRAME_WIDTH: 640,
        CAP_PROP_FRAME_HEIGHT: 480,
    }

    def get_frame(self, pre_fetch=DEFAULT_PRE_FETCH, roi_index=None):
        frame = super().get_frame(pre_fetch)
        if roi_index is not None:
            y0, x0 = self.settings['x0y0'][roi_index]
            dy, dx = self.settings['frame_size'][roi_index]
            frame = frame[y0:y0 + dy, x0:x0 + dx, :]
        return frame

    def dump_frame(self, roi_index=None, filename=None, pre_fetch=DEFAULT_PRE_FETCH):
        frame = self.get_frame(roi_index=roi_index, pre_fetch=pre_fetch)
        if filename is None:
            return
        print(filename, frame.shape)
        imwrite(filename, frame)


def create_camera(index):
    v4l2_base = {
        'brightness': 110,
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
        'exposure_absolute': 10,
    }
    v4l2_config = {
        'dosing': {'brightness': 110, },
        'holder': {'brightness': 150, },
    }
    x0y0 = {
        'dosing': ((200, 240),),
        'holder': ((135, 250),),
    }

    frame_size = {
        'dosing': ((185, 240),),
        'holder': ((128, 170),),
    }

    v4l2 = dict(v4l2_base)
    v4l2.update(v4l2_config[index])

    return CheapCam(SERAIL_NOS[index], config={}, settings={'x0y0': x0y0[index], 'frame_size': frame_size[index]}, v4l2_config=v4l2)
