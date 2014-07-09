def apply_memberfn(memberfn, *args):
  if callable(memberfn):
    return lambda instance: memberfn(instance, *args)
  else:
    return lambda instance: getattr(instance, memberfn)(*args)


def composefn(*functions):
  def rapply(x, fn): return fn(x)
  return lambda x: reduce(rapply, functions, x)
