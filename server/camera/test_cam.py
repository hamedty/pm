import time

import cv2

from camera import cheap_cam

camera1 = cheap_cam.create_camera('dosing')
camera2 = cheap_cam.create_camera('holder')

for i in range(1):
    t0 = time.time()
    frame1 = camera1.get_frame(0)
    frame2 = camera2.get_frame(0)
    print(frame1.shape, frame2.shape, time.time() - t0)

cv2.imwrite('frame1.png', frame1)
cv2.imwrite('frame2.png', frame2)
