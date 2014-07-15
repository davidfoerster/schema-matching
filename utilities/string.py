from __future__ import absolute_import
import locale, unicodedata


def isprint(c):
  return unicodedata.category(c)[0] not in 'CZ'


_char_replacement_sequences = {
   ' ': '<spc>',
  '\n': r'\n',
  '\r': r'\r',
  '\t': r'\t',
  '\v': r'\v',
  '\0': r'\0',
  '\a': r'\a',
  '\b': r'\b',
  '\f': r'\f'
}

def format_char(item):
  if isinstance(item, basestring):
    assert len(item) == 1
    rs = _char_replacement_sequences.get(item)
    if rs is not None:
      return rs
    if isprint(item):
      assert len(format(item, ''))
      return item
    else:
      code = ord(item)
      return \
        ('\\u{:04x}' if code >= 0x80 and isinstance(item, unicode) else '\\x{:02x}') \
          .format(code)
  else:
    return item


# TODO: Use this to frame strings conveniently wherever appropriate
def join(*args):
  strtype = unicode if any((isinstance(s, unicode) for s in args)) else str
  return strtype().join(args)


class DecodableUnicode(unicode):

  default_encoding = locale.getpreferredencoding()


  def __new__(cls, s, encoding=default_encoding, *args):
    return s if isinstance(s, unicode) else unicode.__new__(cls, s, encoding, *args)


  def decode(self, *args):
    return self


  def encode(self, *args):
    return self.sencode(self, *args)


  @staticmethod
  def sencode(self, encoding=default_encoding, *args):
    return unicode.encode(self, encoding, *args)
