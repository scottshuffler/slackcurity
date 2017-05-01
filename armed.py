import os
import time
import RPi.GPIO as GPIO
from time import sleep
from slackclient import SlackClient
from picamera import PiCamera
from imgurpython import ImgurClient

# If you already have an access/refresh pair in hand
client_id = ''
client_secret = ''
access_token = ''
refresh_token = ''

from datetime import datetime

client = ImgurClient(client_id, client_secret, access_token, refresh_token)

GPIO.setmode(GPIO.BCM)
PIR_PIN = 17
GPIO.setup(PIR_PIN, GPIO.IN)

# starterbot's ID as an environment variable
BOT_ID = ''

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "arm"
COMMANDS = ['arm','disarm','temp','test_cam','help']

# instantiate Slack & Twilio clients
slack_client = SlackClient('')

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            #if True:
            if GPIO.input(PIR_PIN):
                try:
                    date = time.strftime("%H-%M-%S")
                    filename = date+'.jpg'
                    #currTime = datetime.now().strftime("%Y-%m-%d-%H-%M-%S.jpg", gmtime())
                    camera = PiCamera()
                    camera.resolution = (1024, 768)
                    camera.start_preview()
                    # Camera warm-up time
                    sleep(2)
                    camera.capture(filename)
                    camera.close()
                    image = client.upload_from_path(filename, config=None, anon=False)
                    response = image.get('link')
                    os.remove(filename)
                    slack_client.api_call("chat.postMessage", channel="#general", text="MOTION DETECTED "+response+"",username='slackarm', icon_emoji=':robot_face:')
                finally:
                    print("Camera error")
            time.sleep(1)

    else:
        print("Connection failed. Invalid Slack token or bot ID?")
