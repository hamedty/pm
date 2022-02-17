cd /home/it/Desktop/PAM2060/server/
# firefox -kiosk http://127.0.0.1:8080/index2 &
(sleep 2; google-chrome --kiosk --app=http://127.0.0.1:8080/index2) &
python3 server.py
