import time

import numpy as np
import cv2

from machine import Machine
from camera import cheap_cam
import vision

machine = Machine()
camera_dosing = cheap_cam.create_camera(0)
camera_holder = cheap_cam.create_camera(1)


def manual_align(camera, key):
    z = 1
    while z:
        frame = camera.get_frame()
        cv2.imwrite('current.png', frame)
        z = input('align, 0 for done')
        try:
            z = int(z)
        except:
            z = 10
        command = {'vh': 1, 'vd': 1, key: z}
        machine.send_command(**command)


def main():
    # machine.bootup()
    manual_align(camera_dosing, 'sd')
    # manual_align(camera_holder, 'sh')
    raise
    frames_dosing = []
    frames_holder = []

    for i in range(400 * 10):
        print(i)
        machine.send_command(vh=1, vd=1, sh=1, sd=1)
        time.sleep(.1)
        frame_dosing = camera_dosing.get_frame()
        frame_holder = camera_holder.get_frame()

        cv2.imwrite('data/dosing_%04d.png' % i, frame_dosing)
        cv2.imwrite('data/holder_%04d.png' % i, frame_holder)

        frames_dosing.append(vision.resize_and_bw(frame_dosing).flatten())
        frames_holder.append(vision.resize_and_bw(frame_holder).flatten())

    frames_dosing = np.array(frames_dosing)
    frames_holder = np.array(frames_holder)

    np.save('frames_dosing.npy', frames_dosing)
    np.save('frames_holder.npy', frames_holder)


main()
