from __future__ import absolute_import, division, print_function, unicode_literals

import os.path

from echomesh.base import Name
from echomesh.base import Path
from echomesh.base import Platform
from echomesh.base import Yaml

def clean(*path):
  return os.path.join(*path).split('/')

def _command_file(*path):
  path = clean(*path)
  if path[0] == 'default':
    return os.path.join(Path.CODE_PATH, 'echomesh', 'config', *path[1:])
  else:
    return os.path.join(Path.PROJECT_PATH, 'command', *path)

COMMAND_PATH = None
def compute_command_path():
  global COMMAND_PATH
  COMMAND_PATH = ([
    'name/' + Name.NAME] +
    [('tag/' + t) for t in Name.TAGS] +
    ['platform/' + Platform.PLATFORM,
     'master',
     _command_file('default/platform/%s' % Platform.PLATFORM),
     _command_file('default')])

compute_command_path()

def expand(*path):
  # These first two lines are to make sure we split on / for Windows and others.
  path = clean(*path)
  return [os.path.join('command', i, *path) for i in COMMAND_PATH]

def resolve(*path):
  x = expand(*path)
  for f in x:
    if os.path.exists(f):
      return f

def load(*path):
  f = resolve(*path)
  if f:
    data = Yaml.read(f)
    if data:
      return data

  raise Exception("Couldn't read Yaml from file %s" % os.path.join(*path))

def config_file(scope):
  return _command_file(scope, 'config.yml')

