import pickle
import cv2
from camera import cheap_cam


class Detector(object):
    def __init__(self):
        # self.camera_dosing = cheap_cam.create_camera(0)
        self.clf_dosing = pickle.load(open('model_dosing.clf', 'rb'))

        self.camera_holder = cheap_cam.create_camera(1)
        self.clf_holder = pickle.load(open('model_holder.clf', 'rb'))

    def detect_dosing(self):
        frame = self.camera_dosing.get_frame()
        cv2.imwrite('current.png', frame)

        d = detect(self.clf_dosing, frame)
        if d != 25:
            d = (d - 0) * -4.0
        else:
            d = 100
        if d < -10:
            d = 400 + d
        return d

    def detect_holder(self):
        frame = self.camera_holder.get_frame()
        d = detect(self.clf_holder, frame)
        d = (d - 2) * -4.0
        return d


DOWNSAMPLE_FACTOR = .5


def resize_and_bw(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    dim = tuple([int(i * DOWNSAMPLE_FACTOR) for i in image.shape[::-1]])
    image = cv2.resize(image, dim, interpolation=cv2.INTER_LINEAR)
    return image


def detect(model, frame):
    frame = resize_and_bw(frame)
    degree = model.predict([frame.flatten()])[0]
    return degree


def main():
    d = Detector()
    print(d.detect_dosing())


if __name__ == '__main__':
    main()
