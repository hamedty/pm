import pickle
import cv2

clf_dosing = pickle.load(open('/home/pi/models/dosing.clf', 'rb'))
clf_holder = pickle.load(open('/home/pi/models/holder.clf', 'rb'))


def detect_dosing(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cls = clf_dosing.predict([frame.flatten()])[0]

    step_per_rev = 32 * 200
    class_per_rev = 100
    p = 1.0 / class_per_rev * step_per_rev

    if cls <= 0:
        steps = -cls * p
    elif cls <= 33:
        steps = (class_per_rev - cls) * p
    else:
        steps = 25 * p

    aligned = abs(cls) < 3

    steps = steps * -1  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!
    return steps, aligned


def detect_holder(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cls = clf_holder.predict([frame.flatten()])[0]

    step_per_rev = 32 * 200
    class_per_rev = 100
    p = 1.0 / class_per_rev * step_per_rev

    steps = -cls * p
    aligned = abs(cls) < 3
    return steps, aligned
