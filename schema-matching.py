#!/usr/bin/python
from __future__ import print_function
import csv, sys, utilities
from collector import (ItemCollectorSet, RowCollector, MultiphaseCollector)
from collector.count import ItemCountCollector
from collector.columntype import ColumnTypeItemCollector


class UnexpectedLineException(Exception):
  def __init__(self, idx, content):
    super(UnexpectedLineException, self).__init__(
      'Unexpected content in line {}: {}'.format(idx, repr(content)))


def main(*argv):
  if len(argv) > 3 and argv[3] != '-':
    sys.stdout = open(argv[3], 'w')

  # TODO: Find useful collector set(s)
  data = [collect(path, ItemCountCollector) for path in argv[1:3]]

  # TODO: Analyse collector results


def collect(path, *collector_types):
  print(path, end=':\n', file=sys.stderr)

  with open(path, 'r') as f:
    data = list(csv.reader(f, delimiter=';', skipinitialspace=True))
    utilities.map_inplace(str.strip, data, 1)

    row_collector = RowCollector((ItemCollectorSet((ColumnTypeItemCollector(len(data)),)) for _ in data[0]))
    row_collector.collect_all(data)
    print(row_collector, file=sys.stderr)
    utilities.each(row_collector.get_transformer(), data)

    row_collector.reset((ItemCollectorSet(collector_types) for _ in data[0]))
    row_collector.collect_all(data) # TODO: Maybe mangle items before collection
    print(row_collector, end='\n\n', file=sys.stderr)

    return data, row_collector


if __name__ == '__main__':
  main(*sys.argv)
