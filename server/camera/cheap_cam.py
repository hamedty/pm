from .base import CameraBase
from cv2 import *

SERAIL_NOS = {
    'holder': '1',
    'dosing': '2',
}

DEFAULT_PRE_FETCH = 4


class CheapCam(CameraBase):
    DEFAULT_PRE_FETCH = DEFAULT_PRE_FETCH
    FILE_FORMAT = '/dev/v4l/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.%s:1.0-video-index0'
    CONFIG_BASE = {
        CAP_PROP_FOURCC: VideoWriter_fourcc('M', 'J', 'P', 'G'),
        CAP_PROP_FRAME_WIDTH: 640,
        CAP_PROP_FRAME_HEIGHT: 480,
    }
    LAST_FRAME = None

    async def async_get_frame(self, *args, **kwargs):
        return self.get_frame(*args, **kwargs)

    def get_frame(self, pre_fetch=DEFAULT_PRE_FETCH, roi_name=None):
        if pre_fetch >= 0:
            self.frame = super().get_frame(pre_fetch)
        if roi_name is not None:
            roi = self.settings['roi'][roi_name]
            x0 = roi['x0']
            x1 = roi['x0'] + roi['dx']
            y0 = roi['y0']
            y1 = roi['y0'] + roi['dy']
            frame = self.frame[y0:y1, x0:x1, :]
        else:
            frame = self.frame
        return frame

    def dump_frame(self, roi_name=None, filename=None, pre_fetch=DEFAULT_PRE_FETCH):
        frame = self.get_frame(roi_name=roi_name, pre_fetch=pre_fetch)
        if filename is None:
            return
        print(filename, frame.shape)
        imwrite(filename, frame)


def create_camera(index, roi):
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
        'exposure_absolute': 18,
    }
    v4l2_config = {
        'dosing': {'brightness': 110, },
        'holder': {'brightness': 150, },
    }

    v4l2 = dict(v4l2_base)
    v4l2.update(v4l2_config[index])

    return CheapCam(SERAIL_NOS[index], config={}, settings={'roi': roi}, v4l2_config=v4l2)


def test():
    holder = create_camera('holder', {})
    filename = '/home/pi/data/test.png'
    holder.dump_frame(filename=filename)
