#!/usr/bin/env python

button_map = {
  '15': 1
}

#####################################################################
import time
import RPi.GPIO as GPIO
from OSC import OSCClient, OSCMessage
import sys
import argparse


def log_uncaught_exceptions(exception_type, exception, tb):
  # print exception_type, exception, tb
  print "Shutting down!"
  exit(1)

client = OSCClient()
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
  while True:
    time.sleep(1)
