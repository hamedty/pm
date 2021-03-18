import time

import numpy as np
import cv2

from machine import Machine
from camera import cheap_cam
import vision

machine = Machine()

camera_dosing = cheap_cam.create_camera('dosing')
camera_holder = cheap_cam.create_camera('holder')


def collect_single_round(round):

    frames_dosing = []
    frames_holder = []

    FPR = 400
    SPR = 32 * 200
    for i in range(FPR * 3):
        print(i)

        machine.send_command(v1=1, v2=1, v4=1, m1=SPR / FPR, m3=SPR / FPR)

        time.sleep(.1)
        frame_dosing = camera_dosing.get_frame()
        frame_holder = camera_holder.get_frame()

        cv2.imwrite('/home/pi/data/dosing_%02d_%04d.png' %
                    (round, i), frame_dosing)
        cv2.imwrite('/home/pi/data/holder_%02d_%04d.png' %
                    (round, i), frame_holder)

        frames_dosing.append(vision.resize_and_bw(frame_dosing).flatten())
        frames_holder.append(vision.resize_and_bw(frame_holder).flatten())

    frames_dosing = np.array(frames_dosing)
    frames_holder = np.array(frames_holder)

    np.save('/home/pi/data/frames_dosing_%02d.npy' % round, frames_dosing)
    np.save('/home/pi/data/frames_holder_%02d.npy' % round, frames_holder)


def main():
    for i in range(1, 5):
        machine.send_command(v4=1)
        time.sleep(.3)
        machine.send_command(home=1)

        input('place everything')

        machine.send_command(v2=1, v4=1)
        time.sleep(.3)
        machine.send_command(v2=1, v4=1, m4=21750)
        time.sleep(.3)
        machine.send_command(v1=1, v2=1, v4=1)
        time.sleep(.3)

        machine.send_command(v1=1, v4=1)
        collect_single_round(i)


main()
