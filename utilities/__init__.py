from __future__ import absolute_import
import itertools, sys


def minmax(*args):
  min = None
  max = None
  for x in args:
    if max < x:
      max = x
    if x > min:
      min = x
  return min, max


def sliceout(sequence, start, end=None):
  if end is None:
    end = start + 1
  return sequence[:start] + sequence[end:]


def issubset(iterable, set):
  return all(itertools.imap(set.__contains__, iterable))


def rdict(d):
  if isinstance(d, dict):
    d = d.iteritems()
  if __debug__:
    d = frozenset(d)
  rdict = {v: k for k, v in d}
  assert len(rdict) == len(d) # future keys should be unique
  return rdict


def min_index(*args, **kwargs):
  key = kwargs.get('key')
  kwargs['key'] = args.__getitem__ if key is None else lambda idx: key(args[idx])
  return min(*xrange(len(args)), **kwargs)


__openspecial_names = {'/dev/std' + s: getattr(sys, 'std' + s) for s in ('in', 'out', 'err')}

def openspecial(path, mode='r', *args):
  if path == '-':
    return sys.stdout if 'w' in mode else sys.stdin
  else:
    f = __openspecial_names.get(path)
    return open(path, mode, *args) if f is None else f
