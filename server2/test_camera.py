import pickle
import cv2
import time
import os
filename = '/dev/v4l/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0-video-index1'
os.system('v4l2-ctl --device=%s --set-fmt-video=width=1280,height=720,pixelformat=MJPG' % filename)
cam = cv2.VideoCapture(filename, apiPreference=cv2.CAP_V4L2)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

model = pickle.load(open('model_dosing.clf', 'rb'))


def detect(image):


    image = image[100:100 + 335, 200:200 + 215, :]
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    dim = tuple([int(i * .5) for i in image.shape[::-1]])
    image = cv2.resize(image, dim, interpolation=cv2.INTER_LINEAR)
    degree = model.predict([image.flatten()])[0]


t0 = time.time()
for i in range(10):
    _, frame = cam.read()
    detect(frame)
    t = time.time()
    print(1 / (t - t0), frame.shape)
    t0 = t

platform - fd500000.pcie - pci - 0000: 01: 00.0 - usb - 0: 1.1: 1.0 - video - index0
platform - fd500000.pcie - pci - 0000: 01: 00.0 - usb - 0: 1.1: 1.0 - video - index1
platform - fd500000.pcie - pci - 0000: 01: 00.0 - usb - 0: 1.2: 1.0 - video - index0
platform - fd500000.pcie - pci - 0000: 01: 00.0 - usb - 0: 1.2: 1.0 - video - index1
