import os
import time
import Adafruit_DHT
import subprocess
from time import sleep
from slackclient import SlackClient
from picamera import PiCamera
from imgurpython import ImgurClient

client_id = ''
client_secret = ''
access_token = ''
refresh_token = ''

from datetime import datetime

album = None # You can also enter an album ID here
image_path = 'Kitten.jpg'

# Note since access tokens expire after an hour, only the refresh token is required (library handles autorefresh)
client = ImgurClient(client_id, client_secret, access_token, refresh_token)

sensor = Adafruit_DHT.AM2302

pin = 4

# starterbot's ID as an environment variable
BOT_ID = ''

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "arm"
COMMANDS = ['arm','disarm','temp','test','help']

# instantiate Slack & Twilio clients
slack_client = SlackClient('')

#armed_pid = -1

def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    #if command.startswith(EXAMPLE_COMMAND):
    if command in COMMANDS:
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
            #proc = subprocess.Popen(["python", "armed.py"]) 
            #armed_pid = proc.pid
            #print(armed_pid)
            response = "Arming, will send images when motion is detected"
        elif command.startswith('disarm'):
            response = "Disarming"
            global armed_pid
            print(armed_pid)
            #os.killpg(armed_pid, signal.SIGTERM)
            armed_pid.terminate()
        elif command.startswith('test'):
            response = "Taking a test picture"
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
            response += " " + image.get('link')
            os.remove(filename)
 
        else:
            response = "List of commands: arm, disarm, temp, test_cam"
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=":robot_face: "+response, as_user=True,icon_emoji=':robot_face:')


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
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
