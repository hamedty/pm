import time
import serial


port = serial.Serial(
    '/dev/serial/by-id/usb-Arduino_Arduino_Due-if00', baudrate=115200)

while True:
    print(port.read(1), end='')
    time.sleep(.01)
