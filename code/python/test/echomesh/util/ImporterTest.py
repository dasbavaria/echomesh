"""

>>> import sys
>>> sys2 = Importer.imp('sys')
>>> assert sys is sys2

>>> koala = Importer.imp('koala')
>>> print_exception(koala)
You requested a feature that needs the Python library "koala".

>>> wombat = Importer.imp('wombat', name='marsupials')
>>> print_exception(wombat)
You requested a feature that needs the Python library "marsupials".

"""

from echomesh.util import Importer

def print_exception(wombat):
  try:
    wombat.test
  except Exception as e:
    print(e)
  else:
    print('FAILED')
