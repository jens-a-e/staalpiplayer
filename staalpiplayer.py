#!/usr/bin/env python

import time
import RPi.GPIO as GPIO
import sys
import subprocess, pipes
from subprocess import call
import dmxout
import argparse
import math
import glob
from os import path
from OSC import OSCServer
from OSC import OSCClient, OSCMessage

parser = argparse.ArgumentParser()

parser.add_argument("-s", default="/dev/ttyUSB0",
  help="The serial port for the Enttec DMX USB Pro box")

parser.add_argument("--serverip", default="127.0.0.1",
  help="The IP to listening on")
parser.add_argument("--serverport", type=int, default=8001,
  help="The port to listening on")

parser.add_argument("--notifierip", default="127.0.0.1",
  help="The IP to listening on")
parser.add_argument("--notifierport", type=int, default=8002,
  help="The port to send notifications to")

parser.add_argument("--statuspin", type=int, default=7,
  help="The status pin to blink on running")

parser.add_argument("--files", default="./midi",
  help="The midi file directory with numbered MIDI files")

parser.add_argument("--map", default="etc/midimap.txt",
  help="A file describing which MIDI note corresponds to which DMX channel(s) - In Max/MSP coll format!")

args = parser.parse_args()

run = False


def get_midi_files():
  """Get an up to date list of files in the set directory"""
  return glob.glob(args.files+"/*.mid")

def get_midi_file(index):
  midi_list = get_midi_files()
  if len(midi_list) > 0:
    return midi_list[index]
  else:
    return None

def song_end():
  global run
  if run is not False:
    print "Song ended."
    run = False
    notifier.send( OSCMessage("/stopped") )

dmx = dmxout.start_dmx(args.s,song_end,args.map)

notifier = OSCClient()
server = OSCServer( (args.serverip, args.serverport) )

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

def shellquote(s):
    return "'" + s.replace("'", "'\\''") + "'"

# RPi.GPIO Layout verwenden (wie Pin-Nummern)
GPIO.setmode(GPIO.BOARD)

def kill_midi():
  call(["pkill","aplaymidi"])

def stop():
  print "Stopping...."
  kill_midi()
  song_end()

def play(file_num):
  global args,run
  run = True
  file = get_midi_file(file_num)
  print "Playing....",file
  kill_midi()
  proc = subprocess.Popen('aplaymidi -p14:0 {}'.format(pipes.quote(file)), shell=True, close_fds=True, stdout=subprocess.PIPE)
  print "\tPID:",proc.pid # Maybe use this to specifically kill a player
  notifier.send( OSCMessage("/playing", path.basename(file), proc.pid) )

# Control LED
GPIO.setup(args.statuspin, GPIO.OUT, initial=GPIO.LOW)

def play_callback(path, tags, args, source):
  """play callback from osc"""
  try:
    play(args[0])
  except Exception,e:
    print "Playing file ", args[0], "failed!", e

def quit_callback(path, tags, args, source):
  stop()

def list_callback(path, tags, args, source):
  """list files callback from osc"""
  try:
    notifier.send( OSCMessage("/files", get_midi_files()) )
  except Exception,e:
    print "List files failed!", e

server.addMsgHandler( "/play", play_callback )
server.addMsgHandler( "/stop", quit_callback )
server.addMsgHandler( "/files", list_callback )

if __name__ == "__main__":
  try:
    notifier.connect( (args.notifierip, args.notifierport) )
    print "StaalPiPlayer Ready."
    print "Resetting system..."
    stop() # reset on boot
    print "Reset done."
    print "\tlistening as:\t"+str(server)
    print "\tsending as:\t"+str(notifier)

    notifier.send( OSCMessage("/files", get_midi_files()) )

    # Dauersschleife
    while 1:
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
