import collections


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


def map_inplace(function, list, depth=0):
  if depth <= 0:
    list[:] = map(function, list)
  else:
    for item in list:
      map_inplace(function, item, depth - 1)


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
  map(lambda item: (f(item) for f in functions), iterable)


def issubset(iterable, set):
  return all(map(set.__contains__, iterable))


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


def head(sequence):
  return sequence[0]


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
