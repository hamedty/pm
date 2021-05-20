import pickle
import cv2

# clf_dosing = pickle.load(open('/home/pi/models/dosing.clf', 'rb'))
clf_holder = pickle.load(open('/home/pi/models/holder.clf', 'rb'))


# def detect_dosing(self, camera):
#     frame = camera.get_frame()
#
#     cls = detect(self.clf_dosing, frame)
#     p = 1 / 100.0 * 200 * 32
#     if cls <= 0:
#         steps = -cls * p
#     elif cls <= 33:
#         steps = (100 - cls) * p
#     else:
#         steps = 25 * p
#
#     aligned = abs(cls) < 3
#
#     return cls, steps, aligned


def detect_holder(frame):
    frame = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cls = model.predict([frame.flatten()])[0]
    prin(cls)

    p = 1 / 100.0 * 200 * 32

    steps = -cls * p
    aligned = abs(cls) < 3
    return steps, aligned
