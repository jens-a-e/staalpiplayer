#!/usr/bin/env python

import time
import RPi.GPIO as GPIO
import sys
import midi
import midi.sequencer as sequencer
import subprocess
from subprocess import call

# RPi.GPIO Layout verwenden (wie Pin-Nummern)
GPIO.setmode(GPIO.BOARD)

global run
run = False


# set up the sequencer
# hardware = sequencer.SequencerHardware()
# 
# if not client.isdigit:
#     client = hardware.get_client(client)
# 
# if not port.isdigit:
#     port = hardware.get_port(port)    

global seq
seq = None


def select_pattern(channel):
  if channel == 15:
    return midi.read_midifile("./midi/1.mid")
  else:
    return None


def stopit(channel):
  global run, seq
  try:
    if seq != None:
      
      e = midi.ControlChangeEvent()
      e.control = 0x7B
      e.value = 0
      seq.event_write(e, True, False, True) # write direct! All notes off
      
      seq.stop_sequencer()
      
      time.sleep(2)
      
      print "Seqencer stopped. waiting...."
      del seq
  except Exception, e:
    # raise e
    pass

def button_press(channel):
  """when a button is pressed"""
  global run, seq
  run = False if run else True
  
  # stopit(channel)
  file = None
  if channel == 15:
    file = "./midi/1.mid"
  
  if run == False or file == None:
    print "Stopping...."
    call(["pkill","aplaymidi"])
    return
  else:
    print "Playing....",file
    proc = subprocess.Popen("aplaymidi -p14:0 "+file,shell=True, stdout=subprocess.PIPE)#, stdout=subprocess.STDOUT, stderr=subprocess.STDOUT)
    print "PID:",proc.pid
    
  
  # pattern = select_pattern(channel)
  # 
  # if pattern == None:
  #   # Bail!!!
  #   return
  # 
  # seq = sequencer.SequencerWrite(sequencer_resolution=pattern.resolution)
  # seq.subscribe_port(14, 0) # Builtin MIDI Through on Linux
  # 
  # if pattern != None:
  #   pattern.make_ticks_abs()
  #   events = []
  #   for track in pattern:
  #     for event in track:
  #       events.append(event)
  #   events.sort()
  #   seq.start_sequencer()
  #   for event in events:
  #     buf = seq.event_write(event, False, False, True)
  #     if buf == None:
  #         continue
  #     if buf < 1000: # Handle error
  #         time.sleep(.5)
  #     if GPIO.input(channel) == GPIO.LOW:
  #       # stop!
  #       run = False
  #       stopit(channel)
  #       print "Stopped within sequence!"
  #       return 
  #   pass
  # print "Done button press!"

# Pin 18 (GPIO 24) auf Input setzen
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(15, GPIO.FALLING, callback=button_press, bouncetime=1000)

# Pin 11 (GPIO 17) auf Output setzen
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
  # stopit(0)
  call(["pkill","aplaymidi"]) # kill all midi players!
  GPIO.cleanup()
  pass
      