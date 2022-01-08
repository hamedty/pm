# read -n 1 -s -r -p "Press any key to continue"
copy_files () {
  rsync -azv --exclude 'dump/' /home/it/Desktop/PAM2060/server/ pi@192.168.44.$1:~/server/
}

copy_models () {
  rsync -avz --progress   /home/it/Desktop/PAM2060/models/holder_$1.clf pi@192.168.44.$1:~/models/holder.clf
  rsync -avz --progress   /home/it/Desktop/PAM2060/models/dosing_$1.clf pi@192.168.44.$1:~/models/dosing.clf
  rsync -avz --progress   /home/it/Desktop/PAM2060/models/cross_section_$1.pickle pi@192.168.44.$1:~/models/cross_section.pickle
}

restart_service () {
  ssh pi@192.168.44.$1 "sudo systemctl restart rpi.service"
}

# # Rail and Robots
# for i in  100
# do
#   echo 192.168.44.$i
#   copy_files $i
#   restart_service $i
# done

# Stations
for i in 102 #101 102 103 104 105 106 107 108 109 110
do
  echo 192.168.44.$i
  copy_files $i
  copy_models $i
  restart_service $i
done

# # Feeder
# for i in  21
# do
#   echo 192.168.44.$i
#   copy_files $i
#   restart_service $i
# done
# echo "Done"
