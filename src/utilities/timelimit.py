import sys, signal

if __debug__:
  from timeit import default_timer as _timer



class Timelimit(object):

  interrupted_flag = None


  def __init__(self, seconds):
    super().__init__()
    self.seconds = seconds


  def __enter__(self):
    if self.seconds > 0:
      if Timelimit.interrupted_flag is not None:
        raise RuntimeError("Multiple time limits aren't supported")
      Timelimit.interrupted_flag = False
      signal.signal(signal.SIGALRM, Timelimit.__timeout_handler)
      if signal.alarm(self.seconds):
        raise RuntimeError('Who set the alarm before us?!!')


  def __exit__(self, exc_type, exc_val, exc_tb):
    if (Timelimit.interrupted_flag):
      print(
        'The time limit of', self.seconds, 'seconds was reached. '
        'The results may be incomplete or inaccurate.',
        file=sys.stderr)
      if __debug__:
        print('INFO:', _timer() - Timelimit.interrupted_flag,
          'seconds between interruption and program termination.',
          file=sys.stderr)

    assert Timelimit.interrupted_flag is not None or not self.seconds
    Timelimit.interrupted_flag = None


  @staticmethod
  def __timeout_handler(signum, frame):
    if signum == signal.SIGALRM:
      Timelimit.interrupted_flag = _timer() if __debug__ else True
