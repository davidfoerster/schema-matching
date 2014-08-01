import utilities.operator as uoperator
from operator import methodcaller
from functools import reduce
from functools import partial as partialfn



def memberfn(memberfn, *args, **kwargs):
  if callable(memberfn):
    return lambda instance: memberfn(instance, *args, **kwargs)
  else:
    return methodcaller(memberfn, *args, **kwargs)


def rapply(arg, function):
  return function(arg)


def composefn(*functions):
  if not functions:
    return uoperator.identity
  if len(functions) == 1:
    return functions[0]
  else:
    return partialfn(reduce, rapply, functions)
