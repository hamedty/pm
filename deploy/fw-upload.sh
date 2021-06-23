# # Robots & Rail
# for i in 100
# do
#   echo 192.168.44.$i
#   scp -rq /home/it/Desktop/g2/g2core/bin/pm-robot/g2core.bin  pi@192.168.44.$i:~/firmware.bin
#   ssh pi@192.168.44.$i "sudo systemctl stop rpi.service"
#   ssh pi@192.168.44.$i "./arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"
#   ssh pi@192.168.44.$i "./arduino-cli upload -p /dev/ttyACM1 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"
#   # ssh pi@192.168.44.$i "./arduino-cli upload -p /dev/ttyACM2 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"
#   ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
# done


# Stations
for i in 101 102 103 104 105
do
  echo 192.168.44.$i
  ssh pi@192.168.44.$i "sudo systemctl stop rpi.service"
  scp -rq /home/it/Desktop/g2/g2core/bin/pm-station/g2core.bin  pi@192.168.44.$i:~/firmware.bin
  ssh pi@192.168.44.$i "./arduino-cli upload -p /dev/ttyACM1 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"
  ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
done
