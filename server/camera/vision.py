import pickle
import cv2

try:
    clf_holder = pickle.load(open('/home/pi/models/holder.clf', 'rb'))
    clf_dosing = pickle.load(open('/home/pi/models/dosing.clf', 'rb'))
except:
    pass  # robot and rail

PRESENCE_THRESHOLD = {'holder': 90, 'dosing': 50}


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

    steps = -cls * p
    aligned = bool(abs(cls) < 2)  # np.bool_ to bool
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
    return bool(value > threshold)


def dosing_sit_right(frame):
    brightness_threshold = 25
    existance_count_threshold = 300
    wrong_sitting_count_threshold = 20
    black_pixel_count = (frame.mean(axis=2).mean(axis=0)
                         < brightness_threshold).sum()
    sit_wrong = existance_count_threshold > black_pixel_count > wrong_sitting_count_threshold
    exist = existance_count_threshold > black_pixel_count
    result = {'sit_right': not sit_wrong, 'exist': bool(exist)}
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

    frame = frame.flatten()
    return frame
