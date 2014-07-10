# coding=utf-8

import re, utilities, itertools, numbers
from numbers import Number
from utilities import infinity
from utilities.iterator import countif
from collector import ItemCollector
from collector.itemcount import ItemCountCollector


__decimal_regex = r"\s*([-+]?)(|\d[^,.]*?|[^,.]*\d|.*?([,.]).*?)\s*$"

def decimal_info(item):
  m = re.match(__decimal_regex, item)
  if not m:
    return None

  start, end = m.span(2)
  if start != len(item) and not (item[start].isdigit() or item[end-1].isdigit()):
    return None

  if start == end:
    sign = m.group(1)
    return ('', len(sign), 0) if not sign or sign == '-' else None

  if start == m.start(3) and end == m.end(3):
    return None

  total_len = end - start
  potential_digits = itertools.islice(item, start, end)
  decimal_separator = m.group(3) if m.start(3) >= 0 else ''
  invalid_char_count = total_len - len(decimal_separator) - \
     countif(type(item).isdigit, potential_digits)
  total_len += m.end(1) - m.start(1)
  return decimal_separator, total_len, invalid_char_count


def tofloat(item):
  assert decimal_info(item)
  if ',' in item:
    item = item.replace(',', '.', 1)
  try:
    return float(item)
  except ValueError:
    return float('NaN')



class ColumnTypeItemCollector(ItemCollector):

  __type_sequence = (long, float, unicode)
  __type_rdict = utilities.rdict(enumerate(__type_sequence))
  __distance_matrix = [
    [
        float(a is not b)
      if isinstance(a, Number) is isinstance(b, Number) else
        infinity
      for a in __type_sequence
    ]
    for b in __type_sequence
  ]

  __transformers = (long, tofloat, utilities.DecodableUnicode)


  @staticmethod
  def __get_set_length(x):
    if isinstance(x, dict):
      icc = x.get(ItemCountCollector)
      x = icc.get_result(x) if icc else None
    assert x is None or isinstance(x, numbers.Integral)
    return x


  def __init__(self, set_length = None, tolerance = (2, 0.25, 0.05)):
    ItemCollector.__init__(self)
    self.__type_index = None
    self.__tol_exceeded_count = 0

    self.__tol_max_invalid_abs, self.__tol_max_invalid_rel, self.__tol_exceeded_max_rel = tolerance
    set_length = self.__get_set_length(set_length)
    self.__total_exceeded_max_abs = \
      None if set_length is None else int(set_length * self.__tol_exceeded_max_rel)


  def collect(self, item, collector_set = None):
    if self.__type_index <= 0: # none or long
      if item == '-' or item.isdigit():
        self.__type_index = 0
        return
      self.__type_index = 1

    if self.__type_index == 1: # float
      info = decimal_info(item)
      if info:
        if not info[2]:
          return
        if info[2] <= self.__tol_max_invalid_abs and info[2] <= info[1] * self.__tol_max_invalid_rel:
          self.__tol_exceeded_count += info[2]
          if not self.__total_exceeded_max_abs < self.__tol_exceeded_count:
            return
      self.__type_index += 1


  def get_result(self, collector_set = None):
    if self.__type_index == 1 and self.__total_exceeded_max_abs is None:
      set_length = self.__get_set_length(collector_set)
      self.__total_exceeded_max_abs = \
        0 if set_length is None else int(set_length * self.__tol_exceeded_max_rel)
      if self.__total_exceeded_max_abs < self.__tol_exceeded_count:
        self.__type_index += 1

    return self.__type_sequence[self.__type_index]


  def get_transformer(self):
    return self.__transformers[self.__type_index]


  @staticmethod
  def result_norm(a, b):
    return (
      ColumnTypeItemCollector.__distance_matrix
        [ColumnTypeItemCollector.__type_rdict[a]]
        [ColumnTypeItemCollector.__type_rdict[b]])


  def as_str(self, collector_set = None, format_spec=None):
    return '({}:{})'.format(self.get_result(None).__name__, self.__tol_exceeded_count)



def factory(string_collector, numeric_collector):

  def __factory(type_or_predecessor):
    if isinstance(type_or_predecessor, dict):
      predecessor = type_or_predecessor
      type = predecessor[ColumnTypeItemCollector].get_result()
    else:
      predecessor = None
      type = type_or_predecessor
    collector = numeric_collector if issubclass(type, Number) else string_collector
    return ItemCollector.get_instance(collector, predecessor)

  return __factory
