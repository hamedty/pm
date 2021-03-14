# reset -> GPOIO21

raspi-gpio set 21 pu
raspi-gpio set 21 op
raspi-gpio set 21 dh
raspi-gpio get 21

sleep .1

./arduino-cli board attach /dev/ttyACM0
./arduino-cli compile --fqbn arduino:sam:arduino_due_x pi
./arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:sam:arduino_due_x pi

ssh-1 "raspi-gpio set 21 dl && sleep .3 && raspi-gpio set 21 dh"



./arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin
