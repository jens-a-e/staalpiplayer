#!/usr/bin/env python

button_map = {
  '15': 1
}

#####################################################################
import time
import sys
import argparse
import RPi.GPIO as GPIO
from OSC import OSCServer
from OSC import OSCClient, OSCMessage


def log_uncaught_exceptions(exception_type, exception, tb):
  # print exception_type, exception, tb
  print "Shutting down!"
  exit(1)

client = OSCClient()
notifications = OSCServer( (args.serverip, args.serverport) )
notifications.timeout = 0
# this method of reporting timeouts only works by convention
# that before calling handle_request() field .timed_out is
# set to False
def handle_timeout(self):
  self.timed_out = True
# funny python's way to add a method to an instance of a class
import types
notifications.handle_timeout = types.MethodType(handle_timeout, notifications)





toggle = False

def button_press(channel):
  """on button down"""
  try:
    global toggle
    toggle = False if toggle else True

    if toggle is True:
      client.send( OSCMessage("/play", button_map[str(channel)] ) )
    else:
      client.send( OSCMessage("/stop" ) )
  except Exception, e:
    pass


def remote_stopped_callback(path, tags, args, source):
  global toggle
  toggle = False

def remote_started_callback(path, tags, args, source):
  pass

if __name__ == "__main__":
  sys.excepthook = log_uncaught_exceptions

  parser = argparse.ArgumentParser()

  parser.add_argument("--ip", default="127.0.0.1",
    help="The IP to send to")
  parser.add_argument("--port", type=int, default=8001,
    help="The port to use")

  args = parser.parse_args()

  # RPi.GPIO Layout verwenden (wie Pin-Nummern)
  GPIO.setmode(GPIO.BOARD)

  GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.add_event_detect(15, GPIO.FALLING, callback=button_press, bouncetime=1000)

  client.connect( (args.ip, args.port) )
  notifications.addMsgHandler( "/stopped", remote_stopped_callback )
  notifications.addMsgHandler( "/playing", remote_started_callback )

  while True:
    try:
      server.timed_out = False
      # handle all pending requests then return
      while not server.timed_out:
        server.handle_request()
      time.sleep(1)
    except Exception, e:
      time.sleep(5)
      pass