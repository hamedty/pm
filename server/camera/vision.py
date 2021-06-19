import pickle
import cv2

try:
    clf_holder = pickle.load(open('/home/pi/models/holder.clf', 'rb'))
    clf_dosing = pickle.load(open('/home/pi/models/dosing.clf', 'rb'))
except:
    pass  # robot and rail


def detect_dosing(frame, offset):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cls = clf_dosing.predict([frame.flatten()])[0] + offset

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
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cls = clf_holder.predict([frame.flatten()])[0] + offset

    step_per_rev = 360
    class_per_rev = 100
    p = 1.0 / class_per_rev * step_per_rev

    steps = -cls * p
    aligned = bool(abs(cls) < 3)  # np.bool_ to bool
    return steps, aligned


def holder_present(frame, direction, x0, dx):
    threshold = 70
    y_margin = 40
    x_margin = 20

    frame = frame[:, x0 + x_margin: x0 + dx - x_margin, :]
    if direction == 'up':
        frame = frame[:y_margin, :, :]
    else:
        frame = frame[-y_margin:, :, :]
    value = frame.mean()
    return bool(value > threshold)


def dosing_present(frame):
    threshold = 50
    value = frame.mean()
    return bool(value > threshold)
