import builtins, argparse



class NargsRangeAction(argparse.Action):

  def __init__(self, option_strings, dest, nargs,
    default=None, type=None, choices=None, required=False, help=None,
    metavar=None
  ):
    assert builtins.type(nargs) is range and len(nargs) > 1
    assert nargs[0] >= 0 and nargs[1] > nargs[0]
    self.nargs_range = nargs

    nargs = argparse.ZERO_OR_MORE if self.nargs_range[0] == 0 else argparse.ONE_OR_MORE
    super().__init__(option_strings, dest, nargs, None, default,
      type, choices, required, help, metavar)


  def __call__(self, parser, namespace, values, option_string=None):
    if len(values) not in self.nargs_range:
      raise argparse.ArgumentError(self.metavar or self.dest,
        "needs {} to {} (multiple of {}) arguments".format(
          self.nargs_range[0], self.nargs_range[-1],
          self.nargs_range[1] - self.nargs_range[0]))

    setattr(namespace, self.dest, values)
