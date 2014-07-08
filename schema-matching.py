#!/usr/bin/python
from __future__ import print_function
import csv, sys, utilities, itertools, operator
import collector
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
  if len(argv) > 3 and argv[3] != '-':
    sys.stdout = open(argv[3], 'w')

  # collector phase description
  collectors = (
    (collector.get_factory(ItemLetterAverageCollector, ItemAverageCollector),),
    (collector.get_factory(LetterStandardDeviationCollector, ItemStandardDeviationCollector),
      collector.get_factory(ItemLetterRelativeFrequencyCollector, None))
  )

  # collect from both input files
  collectors = [collect(path, *collectors) for path in argv[1:3]]

  # The first collector shall have the most columns.
  reversed = len(collectors[0].merged_predecessors) < len(collectors[1].merged_predecessors)
  if reversed:
    collectors.reverse()

  # analyse collected data
  norms = collectors[0].merged_predecessors.results_norms(collectors[1].merged_predecessors)
  if __debug__:
    print(*norms, sep='\n', end='\n\n', file=sys.stderr)

  # find minimal combination
  bestmatch = get_best_schema_mapping(norms)
  if __debug__:
    print('norm:', bestmatch[0], file=sys.stderr)

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

  def get_shortest_path(mapping_so_far, mapping_to_do):
    i = len(mapping_so_far)
    if i == len(distance_matrix):
      return 0, mapping_so_far

    minlength = infinity
    minpath = None
    for j, mapped in enumerate(mapping_to_do):
      d = distance_matrix[i][mapped]
      if d is None or minlength <= d:
        continue

      length, path = get_shortest_path(
        mapping_so_far + (mapped,), utilities.sliceout(mapping_to_do, j))
      if length is None:
        continue

      length += d
      if length < minlength:
        minlength = length
        minpath = path

    return minlength, minpath

  return get_shortest_path(tuple(), tuple(xrange(len(distance_matrix[0]))))



if __name__ == '__main__':
  sys.exit(main(*sys.argv))
