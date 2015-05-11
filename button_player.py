#!/usr/bin/env python
##### settings #######################################################
triggers =(15, 16)

# Timeouts (all in seconds)
# set a timeout per trigger to wait until a new trigger can be engaged
timeouts = (10, 20)

# timeout to reset the system in idle;
# make sure, this timeout is larger than any trigger specific one!
global_timeout = 10*60

start_index = 0
max_track_length = 5 * 60 # set to 5 minutes

#### try loading from the config file ################################
import argparse
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

parser.add_argument("--config", default="/boot/staalplayer/buttons.json", help="Config file to load")

args = parser.parse_args()

import json

try:
  with open(args.config) as json_file:
    data = json.load(json_file)
    try:
      if data['triggers']:
        triggers = data['triggers']
      if data['timeouts']:
        timeouts = data['timeouts']
      if data['global_timeout']:
        global_timeout = data['global_timeout']
      if data['max_track_length']:
        max_track_length = data['max_track_length']
      if data['start_index']:
        start_index = data['start_index']
    except Exception, e:
      print e
except Exception, e:
  "Error loading config file", e
  raise e

##### init settings ##################################################
from datetime import datetime, timedelta

button_map = triggers
timeouts   = [timedelta(seconds=t) for t in timeouts]

global_timeout = timedelta(seconds=global_timeout)

# print the current config:
print "config:"
print "\ttriggers:", triggers
print "\ttimeouts:", timeouts
print "\tglobal_timeout:", global_timeout
print "\tstart_index:", start_index
print "\tmax_track_length:", max_track_length

#####################################################################
import time
import types
import sys

import RPi.GPIO as GPIO

GPIO.setwarnings(False)

from OSC import OSCServer
from OSC import OSCClient, OSCMessage

def log_uncaught_exceptions(exception_type, exception, tb):
  # print exception_type, exception, tb
  print "Shutting down!"
  exit(1)

client = OSCClient()

# Server specific timeout handling:
# this method of reporting timeouts only works by convention
# that before calling handle_request() field .timed_out is
# set to False
def handle_timeout(self):
  self.timed_out = True

# create initial context
state = -2 # -1: idle, other >= 0, correspond to trigger index
running = False
last_play_time = datetime.now()

def button_press(channel):
  """on button down"""
  try:
    global running, global_timeout, last_play_time, state, button_map, timeouts, max_track_length, start_index

    # Map the channel to configured trigger
    index = -1
    try:
      index = button_map.index(channel)
    except Exception, e:
      print "Error, unkown trigger"
      print "Button "+str(channel)+" not in map:", button_map, e
      return
    # if no trigger is set, complain & return
    if index < 0:
      print "Trigger does seem to be configured", channel, index
      return

    # check wether the index is a valid start trigger
    if (state < 0 and index != start_index):
      # print "Invalid start trigger"
      return

    # try to get the timeout for the current state
    try:
      timeout = timeouts[state]
    except Exception, e:
      timeout = 0

    # determine the next state
    next_state = state
    now = datetime.now()

    since = now - last_play_time

    # check for 'after boot' or global timeout
    if state == -2 or since >= global_timeout:
      if index == start_index:
        state = -1
        next_state = index
      else:
        return
    # check for the current state timeout
    elif since >= timeout:
      next_state = index

    # only proceed, if we where in idle or had a transition
    didTransition = False
    if next_state != state:
      running = False # force player restart
      didTransition = True

    if running is not True and didTransition:
      print "Sending play",index
      client.send( OSCMessage("/play", index ) )
      # update the state & context
      state = next_state
      running = True
      # set an assumed stop time to be independent from the player server
      last_play_time = datetime.now() + timedelta(seconds=max_track_length)
      print "Play trigger sent!", last_play_time

    # only, if the toggle option is used
    else:
      if args.toggle:
        client.send( OSCMessage("/stop" ) )

  except Exception, e:
    print "Error on button press:", e
    pass

def remote_stopped_callback(path, tags, args, source):
  global running, last_play_time
  running = False
  last_play_time = datetime.now()
  print "Player stopped", args

def remote_started_callback(path, tags, args, source):
  print "Player started", args
  # global running
  # running = True

def remote_files_callback(path, tags, args, source):
  print "Player has these files:", args


if __name__ == "__main__":
  try:
    sys.excepthook = log_uncaught_exceptions

    notifications = OSCServer( (args.notifierip, args.notifierport) )
    notifications.timeout = 0.1
    # funny python's way to add a method to an instance of a class
    notifications.handle_timeout = types.MethodType(handle_timeout, notifications)

    # RPi.GPIO Layout verwenden (wie Pin-Nummern)
    GPIO.setmode(GPIO.BOARD)

    for _button in button_map:
      GPIO.setup(_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # PUD_DOWN, because we use a pull down resistor, use RISING in next line then!
      GPIO.add_event_detect(_button, GPIO.RISING, callback=button_press, bouncetime=args.bouncetime)

    client.connect( (args.ip, args.port) )
    notifications.addMsgHandler( "/stopped", remote_stopped_callback )
    notifications.addMsgHandler( "/playing", remote_started_callback )
    notifications.addMsgHandler( "/files", remote_files_callback )

    print "StaalPiPlayer Button Client ready!"
    print "\tListening for player with:",notifications
    print "\tSending commands to player with:",client

    while True:
      try:
        notifications.serve_forever()
      except Exception, e:
        time.sleep(5)
        pass

  except Exception, e:
    pass
  finally:
    GPIO.cleanup()
    client.send( OSCMessage("/stop" ) )
    notifications.close()
    pass