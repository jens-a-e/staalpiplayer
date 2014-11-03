import re

class MIDIMapper(object):
  map_re = r'([^,]+?)(?=,)\s*,?\s*(.*?)\s*;$'
  channels_split_re = r'\s*,\s*'

  def __init__(self, map_file):
    self.map_file = map_file
    try:
      self.map = self._parse()
    except Exception, e:
      self.map = {i:(i+1,) for i in range(128)}

  def _parse(self):
    _map = {}
    with open(self.map_file) as f:
      for line in f:
        note, channels = re.match(map_re,line).groups()
        channels = tuple([int(c) for c in re.split(channels_split_re,channels)])
        _map[note]
    return _map

  def _dec_note(self, note_str):


  def to_dmx(self,note):
    """Map a MIDI to a DMX channel"""
    try
    return self.mapping[note]