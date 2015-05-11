#!/usr/bin/env python

##### settings #######################################################

trigger1 = 15
trigger2 = 16

# Timeouts (all in seconds)
# set a timeout per trigger to wait until a new trigger can be engaged
timeout1 = 10
timeout2 = 20

# timeout to reset the system in idle;
# make sure, this timeout is larger than any trigger specific one!
global_timeout = 60


##### init settings ##################################################
from datetime import datetime, timedelta

button_map = ( trigger1, trigger2) # Trigger 1 & Trigger 2
timeouts   = ( timedelta(seconds=timeout1), timedelta(seconds=timeout2) )

global_timeout = timedelta(seconds=global_timeout)

#####################################################################
import time
import types
import sys
import argparse

import RPi.GPIO as GPIO

GPIO.setwarnings(False)

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
    global running, global_timeout, last_play_time, state, button_map, trigger1, trigger2, timeouts

    print "############### button pressed ################"
    print "channel", channel
    print "state", state

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

    # try to get the timeout for the current state
    try:
      timeout = timeouts[index]
    except Exception, e:
      timeout = 0


    # what is the current state?
    # determine the next state
    next_state = state
    now = datetime.now()

    since = now - last_play_time

    print "index", index
    print "time since last play", since
    print "timeout for current state", timeout
    print "timeout checks", (since >= global_timeout), (since >= timeout)

    # check for 'after boot' or global timeout
    if state == -2:
      next_state = 0
    elif since >= global_timeout:
      print "global timeout; setting back to idle"
      next_state = 0 # idle
    # check for the current state timeout
    elif since >= timeout:
      next_state = index
      print "state local timeout; setting to", next_state, state

    # only proceed, if we where in idle or had a transition
    didTransition = False
    if next_state != state:
      print "changing state from", state, "to", next_state
      running = False # force player restart
      didTransition = True

    if running is not True and didTransition:
      print "Sending play",index
      client.send( OSCMessage("/play", index ) )
      # update the state & context
      state = next_state
      running = True
      last_play_time = datetime.now()
      print "Play trigger sent!", last_play_time

    # only, if the toggle option is used
    else:
      if args.toggle:
        client.send( OSCMessage("/stop" ) )

  except Exception, e:
    print "Error on button press:", e
    pass

def remote_stopped_callback(path, tags, args, source):
  global running
  running = False
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