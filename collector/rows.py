from __future__ import absolute_import, print_function
import utilities.operator as uoperator
from . import verbosity
from itertools import imap, ifilter, izip
from utilities.iterator import each
from utilities.functional import memberfn
from utilities.string import join

if verbosity >= 2:
  import sys



class RowCollector(list):
  """Manages collectors for a set of rows"""

  def reset(self, collectors):
    self[:] = collectors


  def collect(self, items):
    """Collects the data of all columns of a row"""
    if verbosity >= 2 and len(self) != len(items):
      print('Row has {} columns, expected {}: {}'.format(len(items), len(self), items), file = sys.stderr)

    assert len(self) <= len(items)
    each(self.__collect_column, self, items)


  @staticmethod
  def __collect_column(collector, item):
    collector.collect(item, collector)


  def collect_all(self, rows):
    each(self.collect, rows)
    each(memberfn('set_collected'), self)


  class __transformer(tuple):

    def __call__(self, items):
      for i, t in self:
        items[i] = t(items[i])


  def get_transformer(self):
    column_transformers = tuple(
      ifilter(uoperator.second,
        enumerate(imap(memberfn('get_transformer'), self))))

    if column_transformers:
      def row_transformer(items):
        for column_idx, column_transformer in column_transformers:
          items[column_idx] = column_transformer(items[column_idx])
    else:
      row_transformer = None

    return row_transformer


  def transform_all(self, rows):
    transformer = self.get_transformer()
    if transformer is not None:
      each(transformer, rows)
      each(memberfn('set_transformed'), self)


  def results_norms(a, b, weights=None):
    get_result = memberfn('get_result')
    # Materialise results of inner loop because they'll be scanned multiple times.
    resultsA = map(get_result, a)
    resultsB = imap(get_result, b)
    return [
      [collB.result_norm(resultA, resultB, weights) for resultA in resultsA]
      for collB, resultB in izip(b, resultsB)
    ]


  def as_str(self, format_spec=''):
    return join('(', u', '.join(imap(memberfn('as_str', None, format_spec), self)), ')')


  def __str__(self): return self.as_str()

  __format__ = as_str
