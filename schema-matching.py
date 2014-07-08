#!/usr/bin/python
from __future__ import print_function
import csv, sys, utilities
import collector
from collector import MultiphaseCollector
from collector.columntype import ColumnTypeItemCollector
from collector.itemaverage import ItemAverageCollector
from collector.letteraverage import ItemLetterAverageCollector
from collector.variance import ItemVarianceCollector
from collector.lettervariance import LetterVarianceCollector
from collector.relativeletterfrequency import ItemLetterRelativeFrequencyCollector


class UnexpectedLineException(Exception):
  def __init__(self, idx, content):
    super(UnexpectedLineException, self).__init__(
      'Unexpected content in line {}: {}'.format(idx, repr(content)))


def main(*argv):
  if len(argv) > 3 and argv[3] != '-':
    sys.stdout = open(argv[3], 'w')

  collectors = (
    (collector.get_factory(ItemLetterAverageCollector, ItemAverageCollector),),
    (collector.get_factory(LetterVarianceCollector, ItemVarianceCollector),
      collector.get_factory(ItemLetterRelativeFrequencyCollector, None))
  )
  collectors = [collect(path, *collectors) for path in argv[1:3]]

  # TODO: Analyse collector results


def collect(path, *phase_descriptions):
  print(path, end=':\n', file=sys.stderr)

  with open(path, 'r') as f:
    multiphasecollector = MultiphaseCollector(
      csv.reader(f, delimiter=';', skipinitialspace=True))
    utilities.map_inplace(str.strip, multiphasecollector.rowset, 1)

    multiphasecollector(ColumnTypeItemCollector(len(multiphasecollector.rowset)))
    print(multiphasecollector.merged_predecessors, file=sys.stderr)

    for phase_description in phase_descriptions:
      multiphasecollector(*phase_description)
      print(multiphasecollector.merged_predecessors, file=sys.stderr)

    print(file=sys.stderr)
    return multiphasecollector


if __name__ == '__main__':
  main(*sys.argv)
