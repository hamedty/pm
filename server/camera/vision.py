import pickle
import cv2

try:
    clf_holder = pickle.load(open('/home/pi/models/holder.clf', 'rb'))
    clf_dosing = pickle.load(open('/home/pi/models/dosing.clf', 'rb'))
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

    steps = -cls * p
    aligned = bool(abs(cls) < 3)  # np.bool_ to bool
    return steps, aligned


def detect_holder(frame, offset):
    frame = prepare_frame(frame, 'holder')
    cls = clf_holder.predict([frame])[0] + offset

    step_per_rev = 360
    class_per_rev = 100
    p = 1.0 / class_per_rev * step_per_rev

    steps = -cls * p
    aligned = bool(abs(cls) < 3)  # np.bool_ to bool
    return steps, aligned


def object_present(frame, threshold):
    threshold = 70
    value = frame.mean()
    return bool(value > threshold)


def prepare_frame(frame, component):
    if component == 'dosing':
        x_downsample = 8
        y_downsample = 2
    elif component == 'holder':
        x_downsample = 2
        y_downsample = 8
    else:
        raise

    x_size = round(frame.shape[1] / x_downsample)
    y_size = round(frame.shape[0] / y_downsample)

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, (x_size, y_size), interpolation=cv2.INTER_AREA)

    frame = frame.flatten()
    return frame
