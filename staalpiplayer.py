#!/usr/bin/env python

import time
import RPi.GPIO as GPIO
import sys
import subprocess
from subprocess import call
import dmxout
import argparse
import math
from OSC import OSCServer

parser = argparse.ArgumentParser()

parser.add_argument("-s", default="/dev/ttyUSB0",
  help="The serial port for the Enttec DMX USB Pro box")
parser.add_argument("--ip", default="127.0.0.1",
  help="The IP to listening on")
parser.add_argument("--port", type=int, default=8001,
  help="The port to listening on")
parser.add_argument("--statuspin", type=int, default=11,
  help="The status pin to blink on running")
parser.add_argument("--files", default="./midi",
  help="The midi file directory with numbered MIDI files")
parser.add_argument("--map", default="etc/midimap.txt",
  help="A file describing which MIDI note corresponds to which DMX channel(s) - In Max/MSP coll format!")

args = parser.parse_args()

run = False

def song_end():
  global run
  run = False

dmx = dmxout.start_dmx(args.s,song_end,args.map)

server = OSCServer( (args.ip, args.port) )

server.timeout = 0
# this method of reporting timeouts only works by convention
# that before calling handle_request() field .timed_out is
# set to False
def handle_timeout(self):
  self.timed_out = True
# funny python's way to add a method to an instance of a class
import types
server.handle_timeout = types.MethodType(handle_timeout, server)


def log_uncaught_exceptions(exception_type, exception, tb):
  global dmx
  dmx.stop()
  print "Shutting down!"
  exit(0)

sys.excepthook = log_uncaught_exceptions


# RPi.GPIO Layout verwenden (wie Pin-Nummern)
GPIO.setmode(GPIO.BOARD)

def stop():
  print
  print "Stopping...."
  call(["pkill","aplaymidi"])
  song_end()


def play(file_num):
  global args,run
  run = True
  file = args.files+"/"+str(file_num)+".mid"
  print "Playing....",file
  proc = subprocess.Popen("aplaymidi -p14:0 "+file,shell=True, stdout=subprocess.PIPE)
  print "PID:",proc.pid # Maybe use this to specifically kill a player


# Control LED
GPIO.setup(args.statuspin, GPIO.OUT, initial=GPIO.LOW)


def play_callback(path, tags, args, source):
  """play callback from osc"""
  try:
    play(args[0])
  except Exception,e:
    print "Playing file ", args[0], "failed!", e

def quit_callback(path, tags, args, source):
  # don't do this at home (or it'll quit blender)
  stop()

server.addMsgHandler( "/play", play_callback )
server.addMsgHandler( "/stop", quit_callback )


try:
  # Dauersschleife
  while 1:
    # LED immer ausmachen
    server.timed_out = False
    # handle all pending requests then return
    while not server.timed_out:
      server.handle_request()

    GPIO.output(args.statuspin, GPIO.LOW)
    # GPIO lesen
    if run:
      # LED an
      GPIO.output(args.statuspin, GPIO.HIGH)

      # Warte 100 ms
      time.sleep(0.1)

      # LED aus
      GPIO.output(args.statuspin, GPIO.LOW)

    # Warte 100 ms
    time.sleep(0.1)

except Exception, e:
  pass
finally:
  stop()
  GPIO.cleanup()
  server.close()
  pass
