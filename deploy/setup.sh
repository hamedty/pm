for i in 101 102 103 104 105 106 107 108 109 110
do
  scp -rq /home/it/Desktop/PAM2060/deploy/boot.sh pi@192.168.44.$i:~/
done
# scp -rq /home/it/Desktop/PAM2060/server/ pi@192.168.44.$i:~/
# ssh pi@192.168.44.$i "rm -r /home/pi/server3"
# ssh pi@192.168.44.$i "rm -r /home/pi/models/*"
# ssh pi@192.168.44.$i "rm -r /home/pi/frame2.png"
# ssh pi@192.168.44.$i "rm -r /home/pi/frame1.png"
# ssh pi@192.168.44.$i "rm /home/pi/models/model_*"
# scp -rq /home/it/Desktop/PAM2060/deploy/bashrc pi@192.168.44.$i:~/.bashrc
# scp -rq /home/it/Desktop/PAM2060/deploy/boot.sh pi@192.168.44.$i:~/

# scp -rq /home/it/Desktop/PAM2060/firmware/.pio/build/due/firmware.bin  pi@192.168.44.$i:~/
# ssh pi@192.168.44.$i "./arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"


# scp -rq /home/it/Desktop/PAM2060/deploy/rpi.service pi@192.168.44.$i:/lib/systemd/system/rpi.service
# ssh pi@192.168.44.$i "sudo chmod 644 /lib/systemd/system/rpi.service"
# ssh pi@192.168.44.$i "sudo systemctl daemon-reload"
# ssh pi@192.168.44.$i "sudo systemctl enable rpi.service"
# ssh pi@192.168.44.$i "sudo reboot"
