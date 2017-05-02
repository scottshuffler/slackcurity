import os
import time
import Adafruit_DHT
import subprocess
from time import sleep
from slackclient import SlackClient
from picamera import PiCamera
from imgurpython import ImgurClient
from os.path import join, dirname
from dotenv import load_dotenv

# Finds .env file and loads it
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Sets up keys from the .env file
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
access_token = os.environ.get("ACCESS_TOKEN")
refresh_token = os.environ.get("REFRESH_ID")
bot_id = os.environ.get("BOT_ID")
slack_secret = os.environ.get("SLACK_SECRET")
disarm_pin = int(os.environ.get("DISARM_PIN"))
AT_BOT = "<@" + bot_id + ">"

# Set up imgue and slack clients
client = ImgurClient(client_id, client_secret, access_token, refresh_token)
slack_client = SlackClient(slack_secret)

# Sets up AM2302 sensor
sensor = Adafruit_DHT.AM2302
pin = 4

# Valid commands
COMMANDS = ['arm', 'disarm', 'temp', 'test', 'help']

armed_pid = -1


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean."
    arr = command.split()
    if arr[0] in COMMANDS:
        if command.startswith('temp'):
            humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
            temperature = ((temperature * 1.8) + 32)
            if humidity is not None and temperature is not None:
                response = 'Temp={0:0.1f}*F  Humidity={1:0.1f}%'.format(temperature, humidity)
            else:
                print('Failed to get reading. Try again!')
        elif command.startswith('arm'):
            global armed_pid
            armed_pid = subprocess.Popen(['python', 'armed.py', ''], shell=False)
            response = "Arming, will send images when motion is detected"
        elif command.startswith('disarm'):
            if len(arr) > 1 and int(arr[1]) == disarm_pin:
                response = "Disarming"
                global armed_pid
                if armed_pid is -1:
                    response = "System not armed"
                else:
                    armed_pid.terminate()
                    armed_pid=-1
            else:
                response = "Pin incorrect, try again"
        elif command.startswith('test'):
            response = "Taking a test picture"
            date = time.strftime("%H-%M-%S")
            filename = date + '.jpg'
            camera = PiCamera()
            camera.resolution = (1024, 768)
            camera.start_preview()
            sleep(2)
            camera.capture(filename)
            camera.close()
            image = client.upload_from_path(filename, config=None, anon=False)
            response += " " + image.get('link')
            os.remove(filename)

        else:
            response = "List of commands: arm, disarm, temp, test_cam"
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=":robot_face: " + response, as_user=True, icon_emoji=':robot_face:')


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


# Look at messages from slack and parse for @slackbot
# When found call handle_command
if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
