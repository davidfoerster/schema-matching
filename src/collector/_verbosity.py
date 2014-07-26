import os


verbosity = os.getenv('VERBOSE', '')
try:
  verbosity = int(verbosity or __debug__)
except ValueError:
  import sys
  print('Warning: Environment variable VERBOSE has unparsable, invalid content:', verbosity, file = sys.stderr)
  verbosity = int(__debug__)
