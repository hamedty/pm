# read -n 1 -s -r -p "Press any key to continue"

# for i in  100
# do
#   echo 192.168.44.$i
#   rsync -az --delete /home/it/Desktop/PAM2060/server/ pi@192.168.44.$i:~/server/
#   ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
# done

# # Stations
# for i in 101 102 103 104 105
# do
#   echo 192.168.44.$i
#   rsync --delete -az /home/it/Desktop/PAM2060/server/ pi@192.168.44.$i:~/server/
#   rsync -avz --progress   /home/it/Desktop/PAM2060/models/holder_$i.clf pi@192.168.44.$i:~/models/holder.clf
#   rsync -avz --progress   /home/it/Desktop/PAM2060/models/dosing_$i.clf pi@192.168.44.$i:~/models/dosing.clf
#   ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
# done

# # Feeder
# for i in  21
# do
#   echo 192.168.44.$i
#   rsync --delete -az /home/it/Desktop/PAM2060/server/ pi@192.168.44.$i:~/server/
#   ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
# done
# echo "Done"
