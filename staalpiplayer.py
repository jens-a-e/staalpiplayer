#!/usr/bin/env python

import time
import RPi.GPIO as GPIO
import sys
import midi
import midi.sequencer as sequencer
import subprocess
from subprocess import call
import dmxout


dmx = dmxout.start_dmx("/dev/ttyUSB1")

def log_uncaught_exceptions(exception_type, exception, tb):
  global dmx
  dmx.stop()
  print
  print "Shutting down!"
  exit(0)
  
sys.excepthook = log_uncaught_exceptions


# RPi.GPIO Layout verwenden (wie Pin-Nummern)
GPIO.setmode(GPIO.BOARD)

global run
run = False

def button_press(channel):
  """when a button is pressed"""
  global run
  run = False if run else True
  
  file = None
  if channel == 15:
    file = "./midi/1.mid"
  
  if run == False or file == None:
    print "Stopping...."
    call(["pkill","aplaymidi"])
    return
  else:
    print "Playing....",file
    proc = subprocess.Popen("aplaymidi -p14:0 "+file,shell=True, stdout=subprocess.PIPE)
    print "PID:",proc.pid # Maybe use this to specifically kill a player
    


GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(15, GPIO.FALLING, callback=button_press, bouncetime=1000)

# Control LED
GPIO.setup(11, GPIO.OUT, initial=GPIO.LOW)


try:
  global run
  # Dauersschleife
  while 1:
    # LED immer ausmachen
    GPIO.output(11, GPIO.LOW)

    global run
    # GPIO lesen
    if run:
      # LED an
      GPIO.output(11, GPIO.HIGH)

      # Warte 100 ms
      time.sleep(0.1)

      # LED aus
      GPIO.output(11, GPIO.LOW)

    # Warte 100 ms
    time.sleep(0.1)

except Exception, e:
  pass
finally:
  call(["pkill","aplaymidi"]) # kill all midi players!
  GPIO.cleanup()
  pass
      