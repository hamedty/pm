import pickle
import cv2

try:
    clf_holder = pickle.load(open('/home/pi/models/holder.clf', 'rb'))
    clf_dosing = pickle.load(open('/home/pi/models/dosing.clf', 'rb'))
except:
    pass  # robot and rail


def detect_dosing(frame, offset):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, (int(
        frame.shape[0] / 10), int(frame.shape[1] / 2)), interpolation=cv2.INTER_LINEAR)
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
    frame = cv2.resize(frame, (int(
        frame.shape[0] / 10), int(frame.shape[1] / 2)), interpolation=cv2.INTER_LINEAR)
    cls = clf_holder.predict([frame.flatten()])[0] + offset

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
