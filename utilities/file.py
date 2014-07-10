from __future__ import absolute_import
import itertools, sys, codecs
from .string import DecodableUnicode


__openspecial_names = {'/dev/std' + s: getattr(sys, 'std' + s) for s in ('in', 'out', 'err')}

def openspecial(path, mode='r', *args):
  if path == '-':
    return sys.stdout if 'w' in mode else sys.stdin
  else:
    f = __openspecial_names.get(path)
    return open(path, mode, *args) if f is None else f
