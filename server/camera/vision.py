import pickle
import cv2
from camera import cheap_cam


class Detector(object):
    N = 1

    def __init__(self):
        self.camera_dosing = cheap_cam.create_camera('dosing')
        self.clf_dosing = pickle.load(
            open('/home/pi/models/model_dosing.clf', 'rb'))

        self.camera_holder = cheap_cam.create_camera('holder')
        self.clf_holder = pickle.load(
            open('/home/pi/models/model_holder.clf', 'rb'))

    def detect_dosing(self):
        frame = self.camera_dosing.get_frame()

        cls = detect(self.clf_dosing, frame)
        p = 1 / 100.0 * 200 * 32
        if cls <= 0:
            steps = -cls * p
        elif cls <= 33:
            steps = (100 - cls) * p
        else:
            steps = 25 * p

        aligned = abs(cls) < 3

        return cls, steps, aligned

    def detect_holder(self):
        frame = self.camera_holder.get_frame()
        # cv2.imwrite('/home/pi/server3/%d.png' % self.N, frame)
        # self.N += 1
        p = 1 / 100.0 * 200 * 32
        cls = detect(self.clf_holder, frame)
        steps = -cls * p
        aligned = abs(cls) < 3
        return cls, steps, aligned


def resize_and_bw(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # dim = tuple([int(i * DOWNSAMPLE_FACTOR) for i in image.shape[::-1]])
    # image = cv2.resize(image, dim, interpolation=cv2.INTER_LINEAR)
    return image


def detect(model, frame):
    frame = resize_and_bw(frame)
    degree = model.predict([frame.flatten()])[0]
    return degree


def main():
    d = Detector()
    while True:
        print(d.detect_holder())
        input('')


if __name__ == '__main__':
    main()
