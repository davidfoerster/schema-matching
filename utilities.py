def each(function, iterable):
  for item in iterable:
    function(item)


def each_unpack(function, iterable):
  for item in iterable:
    function(*item)
