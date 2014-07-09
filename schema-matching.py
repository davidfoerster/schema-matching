#!/usr/bin/python
from __future__ import print_function
import csv, sys, utilities, itertools, operator
import collector, collector.columntype
from collector import MultiphaseCollector
from collector.columntype import ColumnTypeItemCollector
from collector.itemaverage import ItemAverageCollector
from collector.letteraverage import ItemLetterAverageCollector
from collector.variance import ItemStandardDeviationCollector
from collector.lettervariance import LetterStandardDeviationCollector
from collector.relativeletterfrequency import ItemLetterRelativeFrequencyCollector


class UnexpectedLineException(Exception):
  def __init__(self, idx, content):
    super(UnexpectedLineException, self).__init__(
      'Unexpected content in line {}: {}'.format(idx, repr(content)))


def main(*argv):
  """
  :param argv: tuple[str]
  :return: int
  """
  in_paths = [argv[0], argv[1]]
  validate = False
  if len(argv) > 2:
    if argv[2] == '--validate':
      validate = True
    elif argv[2] != '-':
      sys.stdout = open(argv[2], 'w')

  # collector phase description
  collectors = (
    (collector.columntype.factory(
      ItemLetterAverageCollector, ItemAverageCollector),
    ),
    (collector.columntype.factory(
      LetterStandardDeviationCollector, ItemStandardDeviationCollector),
    collector.columntype.factory(
      ItemLetterRelativeFrequencyCollector, None)
    )
  )

  # collect from both input files
  collectors = [collect(path, *collectors) for path in in_paths]

  # The first collector shall have the most columns.
  reversed = len(collectors[0].merged_predecessors) < len(collectors[1].merged_predecessors)
  if reversed:
    collectors.reverse()
    in_paths.reverse()

  # analyse collected data
  norms = MultiphaseCollector.results_norms(*collectors)
  if __debug__:
    print(*norms, sep='\n', end='\n\n', file=sys.stderr)

  # find minimal combination
  best_match = get_best_schema_mapping(norms)
  if __debug__:
    print('norm:', best_match[0], file=sys.stderr)

  # prepare mapping for print
  offset = 1
  mapping = [
    map(str, xrange(offset, len(bestmatch[1]) + offset)),
    map(utilities.composefn(offset.__add__, str), bestmatch[1])
  ]
  if reversed:
    mapping.reverse()
  print(*map(','.join, itertools.izip(*mapping)), sep='\n')

  return 0


def collect(path, *phase_descriptions):
  """
  Collects info about the columns of the data set in file "path" according
  over multiple phases based on a description of those phases.
  """
  if __debug__:
    print(path, end=':\n', file=sys.stderr)

  with open(path, 'r') as f:
    multiphasecollector = MultiphaseCollector(
      csv.reader(f, delimiter=';', skipinitialspace=True))
    utilities.map_inplace(str.strip, multiphasecollector.rowset, 1)

    multiphasecollector(ColumnTypeItemCollector(len(multiphasecollector.rowset)))
    if __debug__:
      print(multiphasecollector.merged_predecessors, file=sys.stderr)

    for phase_description in phase_descriptions:
      multiphasecollector(*phase_description)
      if __debug__:
        print(multiphasecollector.merged_predecessors, file=sys.stderr)
    if __debug__:
      print(file=sys.stderr)

    return multiphasecollector


def get_best_schema_mapping(distance_matrix):
  assert operator.eq(*utilities.minmax(map(len, distance_matrix)))
  infinity = float('inf')

  maxI = len(distance_matrix)
  rangeJ = xrange(len(distance_matrix[0]))
  known_mappings = list(itertools.repeat(None, maxI))
  ismapped = list(itertools.repeat(False, len(rangeJ)))

  def sweep_row(i):
    if i == maxI:
      return 0, tuple(known_mappings)

    minlength = infinity
    minpath = None
    for j in itertools.ifilterfalse(ismapped.__getitem__, rangeJ):
      d = distance_matrix[i][j]
      if d is None or minlength <= d:
        continue

      known_mappings[i] = j
      ismapped[j] = True
      length, path = sweep_row(i + 1)
      ismapped[j] = False
      if path is None:
        continue

      length += d
      if length < minlength:
        minlength = length
        minpath = path

    return minlength, minpath

  return sweep_row(0)



if __name__ == '__main__':
  sys.exit(main(*sys.argv[1:]))
