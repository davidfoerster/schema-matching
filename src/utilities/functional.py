import functools, utilities.operator



def memberfn(memberfn, *args, **kwargs):
  if callable(memberfn):
    return lambda instance: memberfn(instance, *args, **kwargs)
  else:
    return lambda instance: getattr(instance, memberfn)(*args, **kwargs)


def rapply(arg, function):
  return function(arg)


def composefn(*functions):
  if not functions:
    return utilities.operator.identity
  if len(functions) == 1:
    return functions[0]
  else:
    return functools.partial(functools.reduce, rapply, functions)
