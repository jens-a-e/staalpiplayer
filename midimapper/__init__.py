import re

NOTES = ("C","C#","D","D#","E","F","F#","G","G#","A","A#","B")

def _getNoteRange(i):
  return (i/(128/10))%12-2

def _makeNoteName(i):
  _i = _getNoteRange(i)
  return NOTES[i%12] + str( _i ) # if _i != 0 else '')

class MIDIMapper(object):
  map_re = r'([^,]+?)(?=,)\s*,?\s*(.*?)\s*;$'
  channels_split_re = r'\s+'
  notes = {_makeNoteName(i):i for i in range(128)}

  def __init__(self, map_file=None):
    self.map_file = map_file
    self.map = {i:() for i in range(128)} # make a full map of empty mappings
    try:
      self.read(self.map_file)
    except Exception, e:
      if self.map_file is not None:
        print "Could not parse mapping file:",e
      for i in range(128):
        self.map[i] = (i+1,)

  def read(self, filename):
    """Read a mapping file"""
    backup = self.map
    try:
      with open(self.map_file) as f:
        print "Reading midi-map: "+filename
        for line in f:
          note, channels = re.match(self.map_re,line).groups()
          channels = tuple([int(c) for c in re.split(self.channels_split_re,channels)])
          self.map[self.note2dec(note)] = channels
    except Exception, e:
      if filename is not None:
        print "Error reading " + str(filename) + ":", e
      self.map = backup

  def note2dec(self, note_str):
    """Lookup a note value by its standard name (e.g. C-2 up to G8)"""
    return self.notes[note_str]

  def to_dmx(self,note):
    """Map a MIDI to a DMX channel (returns a tuple)"""
    return self.map[note]


# Some quick'n'dirty unit tests...
if __name__=='__main__':
  print MIDIMapper.notes
  mapper = MIDIMapper()
  print mapper.map

  mapper = MIDIMapper("minimap.txt")
  print mapper.map

  mapper = MIDIMapper("default.txt")
  print mapper.map

