import os
import time
import RPi.GPIO as GPIO
import sys
from time import sleep
from slackclient import SlackClient
from picamera import PiCamera
from imgurpython import ImgurClient
from os.path import join, dirname
from dotenv import load_dotenv

# Finds .env file and loads it
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Get keys from .env file
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
access_token = os.environ.get("ACCESS_TOKEN")
refresh_token = os.environ.get("REFRESH_ID")
bot_id = os.environ.get("BOT_ID")
slack_secret = os.environ.get("SLACK_SECRET")
AT_BOT = "<@" + bot_id + ">"

# Create imgur client
client = ImgurClient(client_id, client_secret, access_token, refresh_token)

# Set up PIR sensor
GPIO.setmode(GPIO.BCM)
PIR_PIN = 17
GPIO.setup(PIR_PIN, GPIO.IN)

# Create slack client
slack_client = SlackClient(slack_secret)

channel = sys.argv[1]

# Forever loop, if motion detected it takes a picture, uploads it to imgur and sends the image link to slack chat
if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1
    if slack_client.rtm_connect():
        while True:
            if GPIO.input(PIR_PIN):
                try:
                    date = time.strftime("%H-%M-%S")
                    filename = date + '.jpg'
                    camera = PiCamera()
                    camera.resolution = (1024, 768)
                    camera.start_preview()
                    sleep(2)
                    camera.capture(filename)
                    camera.close()
                    image = client.upload_from_path(filename, config=None, anon=False)
                    response = image.get('link')
                    os.remove(filename)
                    slack_client.api_call("chat.postMessage", channel=channel,
                                          text="MOTION DETECTED " + response + "",as_user=True,
                                          icon_emoji=':robot_face:')
                finally:
                    time.sleep(1)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
