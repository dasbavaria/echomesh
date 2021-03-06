from __future__ import absolute_import, division, print_function #, unicode_literals

import sndhdr

from echomesh.base import Config
from echomesh.expression.Expression import Expression
from echomesh.sound import Aplay
from echomesh.sound import Sound
from echomesh.sound import Util
from echomesh.util import ImportIf
from echomesh.util import Log
from echomesh.util.thread.ThreadLoop import ThreadLoop

numpy = ImportIf.imp('numpy')

LOGGER = Log.logger(__name__)

BITS_PER_BYTE = 8
MAX_DEVICE_NUMBERS = 8

class FilePlayer(ThreadLoop):
  def __init__(self, element, level=1, pan=0, loops=1, **kwds):
    super(FilePlayer, self).__init__(name='FilePlayer')
    from echomesh.sound import SetOutput
    if not SetOutput.OUTPUT_SET:
      SetOutput.set_output()

    self.element = element
    self.file = kwds.pop('file')
    if kwds:
      LOGGER.error('Unused keywords %s', kwds)
    self.debug = True
    self.passthrough = (level == 1 and pan == 0)

    self.level = Expression(level, element)
    self.pan = Expression(pan, element)
    self.loops = loops

    filename = Util.DEFAULT_AUDIO_DIRECTORY.expand(self.file)
    filetype = sndhdr.what(filename)[0]
    handler = Util.FILE_READERS.get(filetype)
    if not handler:
      LOGGER.error("Can't understand the file type of file %s", filename)
      self.pause()
      return

    self.file_stream = handler.open(filename, 'rb')
    self.sample_width = self.file_stream.getsampwidth()

    (self.channels, self.sample_width, self.sampling_rate,
     _, _, _) = self.file_stream.getparams()
    self.dtype = Util.numpy_types()[self.sample_width]
    self.request_channels = 2 if self.pan else self.channels
    self.format = Sound.PYAUDIO().get_format_from_width(self.sample_width)
    self.samples_per_frame = self.sample_width * self.channels
    self.loop_number = 0
    Config.add_client(self)
    self.restart_sound()

  def run(self):
    super(FilePlayer, self).run()

  def config_update(self, get):
    self.frames_per_buffer = get('audio', 'output', 'frames_per_buffer')
    self.chunk_size = get('audio', 'output', 'chunk_size')
    self.index = Sound.get_index_from_config(Sound.OUTPUT, get)

  def open_stream(self):
    try:
      return Sound.PYAUDIO().open(format=self.format,
                                  channels=self.request_channels,
                                  rate=self.sampling_rate,
                                  output=True,
                                  output_device_index=self.index,
                                  frames_per_buffer=self.frames_per_buffer)
    except:
      LOGGER.error('FAILED to open %s on port %s', self.file,
                   Sound.get_device_info(self.index)['name'])
    else:
      LOGGER.info('Opened %s on port %s', self.file,
                  Sound.get_device_info(self.index)['name'])

  def restart_sound(self):
    self._close_stream()
    self.audio_stream = self.open_stream()
    if not self.audio_stream:
      LOGGER.error("Couldn't open sound on loop %d", self.loop_number)
      self.pause()
    self.element.time = 0
    self.current_level = self.level()
    self.current_pan = self.pan()

  def _on_pause(self):
    super(FilePlayer, self)._on_pause()
    self._close_stream()

  def _close_stream(self):
    if getattr(self, 'audio_stream', None):
      self.audio_stream.stop_stream()
      self.audio_stream.close()

  def _convert(self, frames):
    frames = numpy.fromstring(frames, dtype=self.dtype)
    if self.sample_width == 1:
      frames *= 256.0
    elif self.sample_width == 4:
      frames /= 65536.0

    if self.channels == 1:
      return numpy.vstack((frames, numpy.array(frames)))
    else:
      return Util.uninterleave(frames)

  def single_loop(self):
    if not self.audio_stream:
      LOGGER.error('FilePlayer.single_loop terminates')
      # TODO: why should I have to do this given that restart_sound calls pause?
      self.pause()
      return

    frames = self.file_stream.readframes(self.chunk_size)
    if not frames:
      self.loop_number += 1
      if self.loop_number < self.loops:
        self.restart_sound()
        if not self.is_running:
          return
      else:
        self.pause()
        return

    # TODO: below I had written =+ instead of +=!  Does anything change?
    self.element.time += len(frames) / float((self.samples_per_frame *
                                              self.sampling_rate))

    frames = self._pan_and_fade(frames)
    try:
      self.audio_stream.write(frames)
    except:
      if self.is_running:
        raise

  def _pan_and_fade(self, frames):
    if self.passthrough:
      return frames

    left, right = Util.to_numpy(frames, self.dtype,
                                self.sample_width, self.channels)
    if self.level.is_constant():
      left *= self.current_level
      right *= self.current_level
    else:
      next_level = self.level()
      levels = numpy.linspace(self.current_level, next_level, len(left))
      left *= levels
      right *= levels
      self.current_level = next_level

    if self.pan.is_constant():
      lpan, rpan = Util.calculate_pan(self.current_pan)
      left *= lpan
      right *= rpan
    else:
      next_pan = self.pan()
      angles = numpy.linspace(Util.pan_to_angle(self.current_pan),
                              Util.pan_to_angle(next_pan), len(left))

      left *= numpy.cos(angles)
      right *= numpy.sin(angles)
      self.current_pan = next_pan

    return Util.interleave(left, right).tostring()

def play(element, **kwds):
  if 'type' in kwds:
    del kwds['type']
  if 'use_aplay' in kwds:
    use_aplay = kwds['use_aplay']
    del kwds['use_aplay']
  else:
    use_aplay = Config.get('audio', 'output', 'use_aplay')

  return Aplay.play(**kwds) if use_aplay else FilePlayer(element, **kwds)
