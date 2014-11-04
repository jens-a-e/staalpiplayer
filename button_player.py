#!/usr/bin/env python

button_map = (15,16,18)

# This is just for absolute backup, if server did not respond with '/stopped'
play_timeout = timedelta(hours=1)

#####################################################################
import time
import types
import sys
import argparse

import RPi.GPIO as GPIO

from datetime import datetime, timedelta

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
last_button = None
last_play_time = datetime.now()

def button_press(channel):
  """on button down"""
  try:
    global running

    # Check for a timeout of 1 hour to make sure we can play after some time, if missing server packages

    since = datetime.now() - last_play_time

    if since > play_timeout:
      running = False

    if running is False:
      try:
        client.send( OSCMessage("/play", button_map.index(channel) ) )
        running = True
        last_play_time = datetime.now()
      except Exception,e:
        print "Button "+str(channel)+" not in map:", button_map
        pass
    else:
      if args.toggle:
        client.send( OSCMessage("/stop" ) )
  except Exception, e:
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
