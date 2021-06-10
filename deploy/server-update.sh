for i in  101
do
  echo 192.168.44.$i
  rsync -az /home/it/Desktop/PAM2060/server/ pi@192.168.44.$i:~/server/
  # ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
done

# # Stations
# for i in  101 #102 103 104 105
# do
#   echo 192.168.44.$i
#   rsync -az /home/it/Desktop/PAM2060/server/ pi@192.168.44.$i:~/server/
#   # rsync -avz --progress   /home/it/Desktop/PAM2060/models/holder_$i.clf pi@192.168.44.$i:~/models/holder.clf
#   # rsync -avz --progress   /home/it/Desktop/PAM2060/models/dosing_$i.clf pi@192.168.44.$i:~/models/dosing.clf
#   ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
# done
