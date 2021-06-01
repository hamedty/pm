#!/bin/bash

# reset arduino
sleep 5
raspi-gpio set 21 dl
sleep 5
raspi-gpio set 21 dh

sudo rmmod uvcvideo
sudo modprobe uvcvideo nodrop=1 timeout=5000 quirks=0x80
python3 /home/pi/server/rpi.py
