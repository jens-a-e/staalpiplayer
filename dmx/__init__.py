import sys
import serial
import struct
import numpy
import time
import math
import random

class DMXDevice(object):
  DEBUG = False
  def __init__(self, start, length):
    self.start, self.length = start, length
    if start < 1:
      print "DMX Channels must start at least at 1!"
      self.start = 1
    self.blackout()

  def set(self, chan, value):
    """set the value of this channel to value
    (Remember, that DMX channels in start at 1)"""
    if chan >= 1 and chan <= self.length:
      self.values[chan-1] = value
    else:
      if self.DEBUG is not None and self.DEBUG is True:
        print "DMX Device debug: Channel "+str(chan)+" not in range!"

  def blackout(self):
    self.values = [0] * self.length

  def pack(self, buf):
    """modify the passed buffer in place"""
    for index in range(self.length):
      buf[self.start+index] = self.values[index]

  def __str__(self):
    return "<DMXDevice start=%d, length=%d>" % (self.start, self.length)

class DMXManager(object):
  def __init__(self, port, max_channels = 512):
    self.MAX_CHANNELS = max_channels
    self.UNIVERSE = 1
    self.SEND_LABEL = 6
    self.s = serial.Serial(port,57600)
    self.buf = numpy.zeros((self.MAX_CHANNELS + self.UNIVERSE,), dtype='B')
    self.devices = []

  def append(self, device):
    self.devices.append(device)

  def blackout(self):
    for device in self.devices:
      device.blackout()
    self.send()

  def send(self):
    for device in self.devices:
      device.pack(self.buf)
    l = len(self.buf)
    msg = struct.pack("<BBH "+str(l)+"s B",
      0x7e, self.SEND_LABEL, l,
      self.buf.tostring(),
      0xe7
    )
    self.s.write(msg)


if __name__=='__main__':
  port = sys.argv[1]
  manager = DMXManager(port)
  light_0 = DMXDevice(start=25, length=6)
  light_1 = DMXDevice(start=1, length=6)
  manager.append(light_0)
  manager.append(light_1)

  while True:
    intensity = 128*math.sin(time.time())+128
    light_0.set(0, int(intensity))
    light_1.set(1, int(intensity))
    #for light in light_0, light_1:
    #  for color in range(3):
    #    light.set(color, random.randintil.com(0, 255))
    manager.send()
