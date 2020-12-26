import time
from cv2 import *
import os


class CameraBase(object):
    CONFIG_BASE = {}

    def __init__(self, serial_no, config={}, settings={}, v4l2_config={}):
        filename = self.get_webcam_filename(serial_no)
        self._cap = VideoCapture(filename, apiPreference=CAP_V4L2)
        _config = dict(self.CONFIG_BASE)
        _config.update(config)
        for key, value in _config.items():
            self._cap.set(key, value)

        self.settings = dict(settings)
        # dump first frame
        result, _ = self._cap.read()

        # for i in range(2):
        #     for key, value in v4l2_config.items():
        #         command = 'v4l2ctrl --device=%s --set-ctrl=%s=%d' % (
        #             filename, key, value)
        #         os.system(command)
        #
        # result, _ = self._cap.read()
        #
        # assert result

    def get_webcam_filename(self, identifier):
        filename = self.FILE_FORMAT % identifier
        return filename

    def get_frame(self, pre_fetch):
        for i in range(pre_fetch):
            result, _ = self._cap.read()
            assert result
        result, frame = self._cap.read()
        assert result
        return frame


def main():
    r = CameraBase(ALIGNING_2_SN)
    # old_t = time.time()
    #
    # while True:
    #     t1 = time.time()
    #     frame = r.get_frame()
    #     t2 = time.time()
    #     period1 = (t2 - t1) * 1000
    #
    #     new_t = time.time()
    #     period2 = (new_t - old_t) * 1000
    #     old_t = new_t
    #
    #     result = 0  # process(frame)
    #     print(result, '%02d' % period1, '%02d' % period2)
    #     # time.sleep(0.01)

    imwrite('/home/it/Desktop/a.png', r.get_frame())


if __name__ == '__main__':
    main()
