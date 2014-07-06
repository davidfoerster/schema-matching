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


def count_if(function, iterable):
  count = 0
  for item in iterable:
    if function(item):
      count += 1
  return count
