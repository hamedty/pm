from machine import Machine
from camera import cheap_cam
import time

import numpy as np
import cv2

DOWNSAMPLE_FACTOR = .25

camera = cheap_cam.create_camera(0)
machine = Machine()


def save_frame(filename):
    frame = camera.get_frame()
    cv2.imwrite(filename, frame)


def resize_and_bw(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    dim = tuple([int(i * DOWNSAMPLE_FACTOR) for i in image.shape[::-1]])
    image = cv2.resize(image, dim, interpolation=cv2.INTER_LINEAR)
    return image


def manual_align():
    z = 1
    while z:
        save_frame('current.png')
        z = input('align, 0 for done')
        try:
            z = int(z)
        except:
            z = 10
        machine.send_command(vh=1, sh=z)


machine.send_command(vh=1)
time.sleep(1)
manual_align()
frames = []
for i in range(400 * 5):
    print(i)
    machine.send_command(vh=1, sh=1)
    time.sleep(.1)
    frame = camera.get_frame()
    cv2.imwrite('data/test%04d.png' % i, frame)
    frames.append(resize_and_bw(frame).flatten())


frames = np.array(frames)
np.save('holder.npy', frames)
