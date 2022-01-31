import pickle
import cv2
import numpy as np

DOSING_Y_MARGIN = 30


try:
    clf_holder = pickle.load(open('/home/pi/models/holder.clf', 'rb'))
    clf_dosing = pickle.load(open('/home/pi/models/dosing.clf', 'rb'))
    back_cross_section = pickle.load(
        open('/home/pi/models/cross_section.pickle', 'rb'))
except:
    pass  # robot and rail


def detect_dosing(frame, offset):
    frame = prepare_frame(frame, 'dosing')
    cls = clf_dosing.predict([frame])[0] + offset

    step_per_rev = 360
    class_per_rev = 100
    p = 1.0 / class_per_rev * step_per_rev

    if cls <= 0:
        cls = -cls
    elif cls <= 33:
        cls = class_per_rev - cls
    else:
        cls = 25

    steps = -cls * p * .95
    aligned = bool(abs(cls) < 1)  # np.bool_ to bool
    return steps, aligned


def detect_holder(frame, offset):
    frame = prepare_frame(frame, 'holder')
    cls = clf_holder.predict([frame])[0] + offset

    step_per_rev = 360
    class_per_rev = 100
    p = 1.0 / class_per_rev * step_per_rev

    steps = -cls * p
    aligned = bool(abs(cls) < 1)  # np.bool_ to bool
    return steps, aligned


def object_present(frame, threshold):
    value = frame.mean()
    return bool(value > threshold), float(value)


def dosing_sit_right(frame, hw_config_dosing_sit_right):
    # cv2.imwrite('/home/pi/data/sitright.png', frame)
    brightness_threshold = hw_config_dosing_sit_right['brightness_threshold']
    existance_count_threshold = hw_config_dosing_sit_right['existance_count_threshold']
    wrong_sitting_count_threshold = hw_config_dosing_sit_right['wrong_sitting_count_threshold']

    black_pixel_count = (frame.mean(axis=2).mean(axis=0)
                         < brightness_threshold).sum()
    sit_wrong = existance_count_threshold > black_pixel_count > wrong_sitting_count_threshold
    exist = existance_count_threshold > black_pixel_count
    result = {'sit_right': not sit_wrong, 'exist': bool(
        exist), 'black_pixel_count': int(black_pixel_count)}
    return result


def prepare_frame(frame, component):
    if component == 'dosing':
        x_downsample = 8
        y_downsample = 1
    elif component == 'holder':
        x_downsample = 1
        y_downsample = 8
    else:
        raise

    x_size = round(frame.shape[1] / x_downsample)
    y_size = round(frame.shape[0] / y_downsample)

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, (x_size, y_size), interpolation=cv2.INTER_AREA)

    if component == 'dosing':
        offset = active_roi(frame, back_cross_section)
        frame = frame[DOSING_Y_MARGIN + offset:offset - DOSING_Y_MARGIN, :]

    # if component == 'dosing':
    #     mid_point = int(frame.shape[0] / 2)
    #     a = frame[0:mid_point - 55, :].flatten()
    #     b = frame[mid_point + 55:, :].flatten()
    #     frame = np.concatenate([a, b])
    # else:
    frame = frame.flatten()

    return frame


def active_roi(frame, back_cross_section):
    cross_section = frame.mean(axis=1)
    argmax = np.argmax(np.convolve(
        back_cross_section[0], cross_section, mode='same'))
    offset = argmax - back_cross_section[1]

    if abs(offset) > DOSING_Y_MARGIN:
        offset = 0  # fault

    return offset


def dump(frame, filename):
    cv2.imwrite(filename, frame)
