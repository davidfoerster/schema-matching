import sys, signal

if __debug__:
	from timeit import default_timer as _timer
else:
	_timer = None



class Timelimit(object):

	interrupted_flag = None


	def __init__(self, seconds):
		super().__init__()
		self.seconds = seconds


	def __enter__(self):
		if self.seconds > 0:
			if self.interrupted_flag is not None:
				raise RuntimeError("Multiple time limits aren't supported")
			self.interrupted_flag = False
			signal.signal(signal.SIGALRM, self.__timeout_handler)
			if signal.alarm(self.seconds):
				raise RuntimeError('Who set the alarm before us?!!')
		return self


	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.interrupted_flag:
			print(
				'The time limit of {} seconds was reached. The results may be '
					'incomplete or inaccurate.'.format(self.seconds),
				file=sys.stderr)
			if _timer:
				print('INFO:', _timer() - self.interrupted_flag,
					'seconds between interruption and program termination.',
					file=sys.stderr)

		assert self.interrupted_flag is not None or not self.seconds
		self.interrupted_flag = None


	@classmethod
	def __timeout_handler(cls, signum, frame):
		if signum == signal.SIGALRM:
			if _timer:
				cls.interrupted_flag = _timer()
			else:
				cls.interrupted_flag = True
