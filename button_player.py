#!/usr/bin/env python
from datetime import datetime, timedelta

trigger1 = 15
trigger2 = 16

button_map = (trigger1, trigger2) # Trigger 1 & Trigger 2

# Reset to initial state after set timeout
play_timeout = timedelta(minutes=10)

#####################################################################
import time
import types
import sys
import argparse

import RPi.GPIO as GPIO


from OSC import OSCServer
from OSC import OSCClient, OSCMessage

parser = argparse.ArgumentParser()

parser.add_argument("--ip", default="127.0.0.1",
  help="The IP to send to")
parser.add_argument("--port", type=int, default=8001,
  help="The port to use")

parser.add_argument("--notifierip", default="127.0.0.1",
  help="The IP to listening on")
parser.add_argument("--notifierport", type=int, default=8002,
  help="The port to send notifications to")

parser.add_argument("--bouncetime", type=int, default=1000,
  help="Debounce time for the buttons")

parser.add_argument("--toggle", type=bool, default=False,
  help="Switch to toggle play mode (default is fire-and-forget)")

args = parser.parse_args()

def log_uncaught_exceptions(exception_type, exception, tb):
  # print exception_type, exception, tb
  print "Shutting down!"
  exit(1)

client = OSCClient()

# this method of reporting timeouts only works by convention
# that before calling handle_request() field .timed_out is
# set to False
def handle_timeout(self):
  self.timed_out = True

running = False
last_state = "idle"
last_play_time = datetime.now()

def button_press(channel):
  """on button down"""
  try:
    global running, last_play_time, last_state, button_map, trigger1, trigger2

    # Check for a timeout to make sure we can start over after some time
    if datetime.now() - last_play_time > play_timeout:
      print "Player timed out. Sending play anyways..."
      running = False
      last_button = trigger2
      last_state = "idle"

    if running is not True:
      try:
        # Check if button was the same
        if last_button != None && channel == last_button:
          return
        print "Sending play",button_map.index(channel)
        client.send( OSCMessage("/play", button_map.index(channel) ) )
        running = True
        last_play_time = datetime.now()
        last_button = channel
        print "Last play time",last_play_time
      except Exception,e:
        print "Button "+str(channel)+" not in map:", button_map
        pass
    else:
      if args.toggle:
        client.send( OSCMessage("/stop" ) )
  except Exception, e:
    print "Error on button press:",e
    pass

def remote_stopped_callback(path, tags, args, source):
  global running
  running = False
  print "Player stopped", args

def remote_started_callback(path, tags, args, source):
  print "Player started", args
  # global running
  # running = True

if __name__ == "__main__":
  sys.excepthook = log_uncaught_exceptions

  notifications = OSCServer( (args.notifierip, args.notifierport) )
  notifications.timeout = 0.1
  # funny python's way to add a method to an instance of a class
  notifications.handle_timeout = types.MethodType(handle_timeout, notifications)

  # RPi.GPIO Layout verwenden (wie Pin-Nummern)
  GPIO.setmode(GPIO.BOARD)

  for _button in button_map:
    GPIO.setup(_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(_button, GPIO.FALLING, callback=button_press, bouncetime=args.bouncetime)

  client.connect( (args.ip, args.port) )
  notifications.addMsgHandler( "/stopped", remote_stopped_callback )
  notifications.addMsgHandler( "/playing", remote_started_callback )

  print "StaalPiPlayer Button Client ready!"
  print "\tListening for player with:",notifications
  print "\tSending commands to player with:",client

  while True:
    try:
      notifications.serve_forever()
    except Exception, e:
      time.sleep(5)
      pass
