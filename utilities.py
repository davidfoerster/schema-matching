import __builtin__, collections, itertools, sys


def each(function, iterable):
  for item in iterable:
    function(item)


def each_unpack(function, iterable):
  for item in iterable:
    function(*item)


def minmax(*args):
  min = None
  max = None
  for x in args:
    if max < x:
      max = x
    if x > min:
      min = x
  return min, max


def __slice_to_tuple(slice):
  return (slice.start, slice.stop, slice.step)


def islice(iterable, *args):
  if not args:
    args = (None,)
  elif isinstance(args[0], slice):
    assert len(args) == 1
    args = __slice_to_tuple(args[0])
  return itertools.islice(iterable, *args)


def map_inplace(function, list, depth=0, slice=None):
  if depth <= 0:
    if slice is None:
      list[:] = itertools.imap(function, list)
    else:
      list[slice] = itertools.imap(function,
        itertools.islice(list, __slice_to_tuple(slice)))
  else:
    for item in list:
      map_inplace(function, item, depth - 1, slice)
  return list


def sliceout(sequence, start, end=None):
  if end is None:
    end = start + 1
  return sequence[:start] + sequence[end:]


def count_if(function, iterable):
  count = 0
  for item in iterable:
    if function(item):
      count += 1
  return count


def teemap(iterable, *functions):
  return itertools.imap(lambda item: [item if f is None else f(item) for f in functions], iterable)


def issubset(iterable, set):
  return all(itertools.imap(set.__contains__, iterable))


def apply_memberfn(memberfn, *args):
  if callable(memberfn):
    return lambda instance: memberfn(instance, *args)
  else:
    return lambda instance: getattr(instance, memberfn)(*args)


def composefn(*functions):
  def rapply(x, fn): return fn(x)
  return lambda x: reduce(rapply, functions, x)


def getitemfn(idx):
  return lambda seq: seq[idx]


def first(sequence):
  return sequence[0]


def second(sequence):
  return sequence[1]


def isnone(x):
  return x is None


def rdict(dict):
  if isinstance(dict, __builtin__.dict):
    dict = dict.iteritems()
  if __debug__:
    dict = frozenset(dict)
  rdict = {v: k for k, v in dict}
  assert len(rdict) == len(dict) # future keys should be unique
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


class ProbabilityDistribution(collections.defaultdict):
  """"Holds a probability distribution and can compute the distance to other dists"""

  def __init__(self, *args):
    collections.defaultdict.__init__(self, int, *args)


  def get(self, k, d = 0):
    return dict.get(self, k, d)


  def distance_to(self, compare_to):
    return sum(
      (abs(self.get(bin) - compare_to.get(bin))
        for bin in self.viewkeys() | compare_to.viewkeys()),
      0)
