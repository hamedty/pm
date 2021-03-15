import time

import numpy as np
import cv2

from machine import Machine
from camera import cheap_cam
import vision

machine = Machine()
camera = cheap_cam.create_camera(0)


def main():
    # machine.send_command(v2=1)
    machine.send_command(v1=1, v4=1)

    frames = []

    FPR = 400
    SPR = 6400
    for i in range(FPR * 10):
        print(i)
        # machine.send_command(v2=1, m3=SPR / FPR)
        machine.send_command(v1=1, v4=1, m1=SPR / FPR)

        time.sleep(.1)
        frame = camera.get_frame()

        cv2.imwrite('/home/pi/data/dosing_%04d.png' % i, frame)
        # cv2.imwrite('/home/pi/data/holder_%04d.png' % i, frame)

        frames.append(vision.resize_and_bw(frame).flatten())

    frames = np.array(frames)

    np.save('/home/pi/data/frames_dosing.npy', frames)
    # np.save('/home/pi/data/frames_holder.npy', frames)


main()
