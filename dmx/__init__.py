import sys
import serial
import struct
import numpy
import time
import math
import random

class DMXDevice(object):
  def __init__(self, start, length):
    self.start, self.length = start, length
    self.values = [0] * self.length

  def set(self, chan, value):
    """set the value of this channel to value (relative channel number)"""
    self.values[chan] = value

  def pack(self, buf):
    """modify the passed buffer in place"""
    for index in range(self.length):
      buf[self.start+index] = self.values[index]

  def __str__(self):
    return "<DMXDevice start=%d, length=%d>" % (self.start, self.length)

class DMXManager(object):
  def __init__(self, port):
    self.s = serial.Serial(port)
    self.buf = numpy.zeros((128,), dtype='B')
    self.devices = []

  def append(self, device):
    self.devices.append(device)

  def send(self):
    for device in self.devices:
      device.pack(self.buf)

    msg = struct.pack("<BBH 128s B",
      0x7e, 6, 128, 
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
