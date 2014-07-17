from __future__ import absolute_import
import unicodedata



basestring = (str, bytes)


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
        ('\\u{:04x}' if code >= 0x80 and isinstance(item, str) else '\\x{:02x}') \
          .format(code)
  else:
    return item


def join(*args):
  return ''.join(args)
