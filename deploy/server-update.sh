# read -n 1 -s -r -p "Press any key to continue"
copy_files () {
  rsync --delete -azv --exclude 'dump/' /home/it/Desktop/PAM2060/server/ pi@192.168.44.$1:~/server/
}


# Rail and Robots
for i in  100
do
  echo 192.168.44.$i
  copy_files $i
  ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
done

# Stations
for i in 101 102 103 104 105 106 107 108 109 110
do
  echo 192.168.44.$i
  copy_files $i
  # rsync -avz --progress   /home/it/Desktop/PAM2060/models/holder_$i.clf pi@192.168.44.$i:~/models/holder.clf
  # rsync -avz --progress   /home/it/Desktop/PAM2060/models/dosing_$i.clf pi@192.168.44.$i:~/models/dosing.clf
  ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
done

# Feeder
for i in  21
do
  echo 192.168.44.$i
  copy_files $i
  ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
done
echo "Done"
