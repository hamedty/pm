set -e

cd /home/it/Desktop/g2/g2core
ssh pi@192.168.44.100 "killall python3"
make PLATFORM=DUE BOARD=gShield
scp /home/it/Desktop/g2/g2core/bin/gShield/g2core.elf pi@192.168.44.100:~/
ssh pi@192.168.44.100 "sudo systemctl stop rpi.service"
ssh pi@192.168.44.100 "raspi-gpio set 21 dl && sleep 2 && raspi-gpio set 2 dh && sleep 2"
ssh pi@192.168.44.100 "./arduino-cli upload -p /dev/ttyACM1 --fqbn arduino:sam:arduino_due_x --input-file g2core.elf"
ssh pi@192.168.44.100 "raspi-gpio set 2 dl && sleep 2 && raspi-gpio set 2 dh && sleep 2"
ssh pi@192.168.44.100 "python3 ~/a.py -p /dev/serial/by-path/platform-fd500000.pcie-pci-0000\:01\:00.0-usb-0\:1.1\:1.0 115200 -l 0.0.0.0 --access-list='192.168.44.1'"

python3 ~/a.py -p /dev/ttyACM0 115200 -l 0.0.0.0 --access-list='192.168.44.1
