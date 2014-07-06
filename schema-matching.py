#!/usr/bin/python
from __future__ import print_function
import csv, sys
from collector import *
from collector.count import ItemCountCollector
from collector.letteraverage import ItemLetterAverageCollector

class UnexpectedLineException(Exception):
  def __init__(self, idx, content):
    super(UnexpectedLineException, self).__init__(
      'Unexpected content in line {}: {}'.format(idx, repr(content)))


def main(*argv):
  if len(argv) > 3 and argv[3] != '-':
    sys.stdout = open(argv[3], 'w')

  # TODO: Find useful collector set(s)
  data = [collect(path, ItemCountCollector, ItemLetterAverageCollector) for path in argv[1:3]]

  # TODO: Analyse collector results
  print(str(data[0][1]), str(data[1][1]), sep='\n', file=sys.stderr)


def collect(path, *collector_types):
  with open(path, 'r') as f:
    data = list(csv.reader(f, delimiter=';', skipinitialspace=True))
    row_collector = RowCollector((ItemCollectorSet(collector_types) for _ in data[0])) # TODO: does this work as expected?
    utilities.each_unpack(row_collector.collect, data) # TODO: Maybe mangle items before collection
    return data, row_collector


if __name__ == '__main__':
  main(*sys.argv)
