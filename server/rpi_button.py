import requests
import RPi.GPIO as GPIO
import time


def isr_press(channel):
    global in_press, press_start
    if GPIO.input(20) == 0:  # pressed
        if in_press:
            return
        in_press = True
        press_start = time.time()
    else:  # unpress
        if not in_press:
            return
        duration = time.time() - press_start
        if duration < .05:
            return
        in_press = False
        post_press_data(duration)


def post_press_data(duration):
    message = {
        'type': 'button_press',
        'duration': duration
    }
    post_data(message)


def post_data(message):
    url = 'http://192.168.44.1:8080/rpi'
    requests.post(url, json=message)


def main():
    global in_press, press_start
    press_start = 0
    in_press = False

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(20, GPIO.BOTH, callback=isr_press)

    while (True):
        time.sleep(1)


if __name__ == "__main__":
    main()
