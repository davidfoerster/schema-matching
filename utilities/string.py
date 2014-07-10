from __future__ import absolute_import
import locale, unicodedata


def isprint(c):
  return unicodedata.category(c)[0] not in 'CZ'


def char_repr(c):
  if isprint(c):
    assert len(format(c, ''))
    return c
  else:
    code = ord(c)
    return \
      ('\\u{:04x}' if isinstance(c, unicode) and code >= 0x80 else '\\x{:02x}') \
        .format(code)


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
