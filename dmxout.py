import time
from dmx import DMXDevice
from dmx import DMXManager
from midimapper import MIDIMapper
import sys
import midi
import midi.sequencer as sequencer
from thread import start_new_thread, allocate_lock
import threading

def vel2val(velocity):
  return int(255/127.0 * velocity)

def log_uncaught_exceptions(exception_type, exception, tb):
  print "log exception",exception_type, exception, tb

sys.excepthook = log_uncaught_exceptions

class dmx_runner(threading.Thread):

  def __init__ (self, port, end_callback, midi_map):
    super(dmx_runner, self).__init__()
    self.mapper = MIDIMapper(midi_map)
    self.end_callback = end_callback
    self._stop = threading.Event()
    self.port = port
    self.client = 14
    self.midiport = 0
    self.seq = None
    self.channels = 128
    self.manager = DMXManager(self.port,self.channels)
    self.default = DMXDevice(start=1, length=self.channels) # TODO: load from config!
    self.manager.append(self.default)

  def stop(self):
    self._stop.set()

  def stopped(self):
    return self._stop.isSet()

  def _blackout(self):
    for channel in range(self.channels):
      self.default.set(channel, 0)
    self.manager.send()

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
              value = vel2val(event.velocity) if isinstance(event, midi.NoteOnEvent) else 0
              for channel in self.mapper.to_dmx(event.pitch):
                self.default.set(channel, value)
            elif isinstance(event,midi.ControlChangeEvent):
              if event.control is 0x7B or (event.control is 120 and event.value is 0):
                self._blackout()
                if self.end_callback is not None:
                  self.end_callback()
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
      self._blackout()
      pass

main_dmx = None

def start_dmx(port,end_callback,midi_map):
  main_dmx = dmx_runner(port,end_callback,midi_map)
  main_dmx.start()
  return main_dmx

