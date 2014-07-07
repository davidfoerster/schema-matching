import re, utilities, itertools
from numbers import Number
from collector import ItemCollector
from collector.count import ItemCountCollector


def decimal_info(item):
  m = re.match(r"\s*([-+]?)(|\d[^,.]*?|[^,.]*\d|.*?([,.]).*?)\s*$", item)
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
     utilities.count_if(str.isdigit, potential_digits)
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

  __type_sequence = (None, long, float, str)
  __transformers = (None, long, tofloat, str)


  @staticmethod
  def __get_set_length(x):
    if isinstance(x, dict):
      icc = x.get(ItemCountCollector)
      x = icc.get_result(x) if icc else None
    assert x is None or isinstance(x, int)
    return x


  def __init__(self, set_length = None, tolerance = (2, 0.25, 0.05)):
    ItemCollector.__init__(self)
    self.__type_index = 0
    self.__tol_exceeded_count = 0

    self.__tol_max_invalid_abs, self.__tol_max_invalid_rel, self.__tol_exceeded_max_rel = tolerance
    set_length = self.__get_set_length(set_length)
    self.__total_exceeded_max_abs = \
      None if set_length is None else int(set_length * self.__tol_exceeded_max_rel)


  def collect(self, item, collector_set = None):
    if self.__type_index <= 1: # None or long
      if item == '-' or item.isdigit():
        self.__type_index = 1
        return
      self.__type_index = 2

    if self.__type_index == 2: # float
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
    if self.__type_index == 2 and self.__total_exceeded_max_abs is None:
      set_length = self.__get_set_length(collector_set)
      self.__total_exceeded_max_abs = \
        0 if set_length is None else int(set_length * self.__tol_exceeded_max_rel)
      if self.__total_exceeded_max_abs < self.__tol_exceeded_count:
        self.__type_index += 1

    return self.__type_sequence[self.__type_index]


  def get_transformer(self):
    return self.__transformers[self.__type_index]


  def as_str(self, collector_set = None):
    return '({}, {})'.format(self.get_result(None).__name__, self.__tol_exceeded_count)



class get_factory(object):

  def __init__(self, string_collector, numeric_collector):
    object.__init__(self)
    self.collectors = (string_collector, numeric_collector)


  def __call__(self, predecessor):
    valuetype = (
        predecessor[ColumnTypeItemCollector].get_result()
      if isinstance(predecessor, dict) else
        predecessor
    )
    return ItemCollector.get_instance(
      self.collectors[issubclass(valuetype, Number)], predecessor)
