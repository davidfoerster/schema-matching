from __future__ import absolute_import, print_function
import os
from .base import ItemCollector


verbosity = os.getenv('VERBOSE', '')
try:
  verbosity = int(verbosity or __debug__)
except ValueError:
  import sys
  print('Warning: Environment variable VERBOSE has unparsable, invalid content:', verbosity, file = sys.stderr)
  verbosity = int(__debug__)
