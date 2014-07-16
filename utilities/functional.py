import functools
import operator


def memberfn(memberfn, *args):
  if callable(memberfn):
    return lambda instance: memberfn(instance, *args)
  else:
    return lambda instance: getattr(instance, memberfn)(*args)


def rapply(arg, function):
  return function(arg)


def composefn(*functions):
  if not functions:
    return operator.identity
  if len(functions) == 1:
    return functions[0]
  else:
    return functools.partial(reduce, rapply, functions)
