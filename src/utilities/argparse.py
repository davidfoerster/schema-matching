import builtins, sys, argparse, itertools



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



class ChoicesRangeHelpFormatter(argparse.HelpFormatter):

	def _expand_help(self, action):
		params = {
			k: getattr(v, '__name__', v)
			for k, v in vars(action).items()
			if v is not argparse.SUPPRESS
		}
		if self._prog is not argparse.SUPPRESS:
			params['prog'] = getattr(self._prog, '__name__', self._prog)

		choices = params.get('choices')
		if choices is not None:
			if type(choices) is range:
				if choices[-1] == sys.maxsize - 1:
					choices_str = '≥' + str(choices[0])
				else:
					choices_str = str(choices[0]) + '-' + str(choices[-1])
					step = choices[1] - choices[0]
					if abs(step) != 1:
						choices_str += ' step: ' + str(step)
			else:
				choices_str = ', '.join((str(c) for c in choices))
			params['choices'] = choices_str
		return self._get_help_string(action) % params



class NargsRangeHelpFormatter(argparse.HelpFormatter):

	def _format_args(self, action, default_metavar):
		if not isinstance(action, NargsRangeAction):
			return super()._format_args(action, default_metavar)

		nargs = action.nargs_range
		assert type(nargs) is range
		if len(nargs) <= 1 or nargs[-1] != sys.maxsize - 1:
			return NotImplemented

		assert nargs[0] >= 0
		assert nargs[1] - nargs[0] > 0
		metavar = self._metavar_formatter(action, default_metavar)(1)[0]
		return '{} [{} ...]'.format(
			' '.join(itertools.repeat(metavar, nargs[0])),
			' '.join(itertools.repeat(metavar, nargs[1] - nargs[0])))



class CombinedCustomHelpFormatter(ChoicesRangeHelpFormatter, NargsRangeHelpFormatter):

	_expand_help = ChoicesRangeHelpFormatter._expand_help

	_format_args = NargsRangeHelpFormatter._format_args
