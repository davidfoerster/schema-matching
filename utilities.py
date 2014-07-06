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


def map_inplace(function, list, depth = 0):
  if depth <= 0:
    list[:] = map(function, list)
  else:
    for item in list:
      map_inplace(function, item, depth - 1)


def count_if(function, iterable):
  count = 0
  for item in iterable:
    if function(item):
      count += 1
  return count
