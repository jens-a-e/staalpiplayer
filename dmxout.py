import time
from dmx import DMXDevice
from dmx import DMXManager
import sys
import midi
import midi.sequencer as sequencer
from thread import start_new_thread, allocate_lock
import threading

import sys

def log_uncaught_exceptions(exception_type, exception, tb):
  print "log exception",exception_type, exception, tb

sys.excepthook = log_uncaught_exceptions

class dmx_runner(threading.Thread):

  def __init__ (self, port):
    # threading.Thread.__init__(self)
    super(dmx_runner, self).__init__()
    self._stop = threading.Event()
    self.port = port
    self.client = 14
    self.midiport = 0
    self.seq = None
    self.channels = 127 # TODO fix in dmx module to 512 max (actually 512 + 1 universe)
    self.manager = DMXManager(self.port)
    self.default = DMXDevice(start=1, length=self.channels) # TODO: load from config!
    self.manager.append(self.default)

  def stop(self):
    self._stop.set()

  def stopped(self):
    return self._stop.isSet()

  def run(self):
    if self.seq is not None:
      self.seq.stop_sequencer()
      del self.seq

    self.seq = sequencer.SequencerRead(sequencer_resolution=120)
    self.seq.subscribe_port(self.client, self.midiport)
    self.seq.start_sequencer()

    # sys.excepthook = lambda *args: None
    try:
      while True:
        try:
          hasEvents = True
          while hasEvents:
            event = self.seq.event_read()
            if event is None:
              hasEvents = False
              break
            if isinstance(event, midi.NoteEvent):
              channel = event.pitch # TODO: mapping goes here
              if isinstance(event, midi.NoteOnEvent):
                value = event.velocity * 2
              if isinstance(event, midi.NoteOffEvent):
                value = 0
              if channel < self.channels:
                self.default.set(channel, value)
              else:
                print "target channel to high", channel, self.channels
            elif isinstance(event,midi.ControlChangeEvent):
              if event.control is 0x7B or (event.control is 120 and event.value is 0):
                for channel in range(self.channels):
                  self.default.set(channel, 0)
        except Exception, e:
          # raise e
          print "Error on sending DMX", e
          time.sleep(1)
          pass # on exception
        # else:
        #   pass
        finally:
          if self.stopped():
            raise threading.ThreadError("Stop DMX!")
          else:
            self.manager.send()
            time.sleep(0.025) # ~40FPS
          pass
        
    except Exception, e:
      # Main thread exception catching
      print "On terminate",e
      pass # on exception
    finally:
      print "Terminating DMX. Sending Blackout"
      for channel in range(self.channels):
        self.default.set(channel, 0)
      self.manager.send() # TODO: Implement as blackout in dmx module!
      pass

main_dmx = None

def start_dmx(port):
  main_dmx = dmx_runner(port)
  main_dmx.start()
  return main_dmx

