#!/usr/bin/python
from __future__ import print_function
import csv, sys, utilities
import collector
from collector import MultiphaseCollector
from collector.count import ItemCountCollector
from collector.sum import ItemSumCollector
from collector.lettercount import ItemLetterCountCollector
from collector.columntype import ColumnTypeItemCollector


class UnexpectedLineException(Exception):
  def __init__(self, idx, content):
    super(UnexpectedLineException, self).__init__(
      'Unexpected content in line {}: {}'.format(idx, repr(content)))


def main(*argv):
  if len(argv) > 3 and argv[3] != '-':
    sys.stdout = open(argv[3], 'w')

  # TODO: Find useful collector set(s)
  collectors = [collect(path, collector.get_factory(ItemLetterCountCollector, ItemSumCollector)) for path in argv[1:3]]

  # TODO: Analyse collector results


def collect(path, *collector_types):
  print(path, end=':\n', file=sys.stderr)

  with open(path, 'r') as f:
    multiphasecollector = MultiphaseCollector(
      csv.reader(f, delimiter=';', skipinitialspace=True))
    utilities.map_inplace(str.strip, multiphasecollector.rowset, 1)

    multiphasecollector(ColumnTypeItemCollector(len(multiphasecollector.rowset)))
    print(multiphasecollector.merged_predecessors, file=sys.stderr)

    multiphasecollector(*collector_types)
    print(multiphasecollector.merged_predecessors, end='\n\n', file=sys.stderr)

    return multiphasecollector


if __name__ == '__main__':
  main(*sys.argv)
