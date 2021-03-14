import cv2
from camera import cheap_cam


cam = cheap_cam.create_camera(0)
frame = cam.get_frame()
print(frame.shape)
cv2.imwrite('/home/pi/a.png', frame)
