# -*- coding: utf-8 -*-
# to remove if we decide to add a dependency on six or future
# very strongly inspired by https://github.com/pallets/werkzeug/blob/master/werkzeug/_compat.py
#pylint: disable=deprecated-module
import sys
import odoo
from odoo.tools import pycompat

PY2 = sys.version_info[0] == 2

# https://mothereff.in/utf-8
SPECIAL_CHARACTER_BYTES_LS = ls = [
    b'\x00', b'\x01', b'\x02', b'\x03', b'\x04', b'\x05', b'\x06', b'\x07',
    b'\x08', b'\x0B', b'\x0C', b'\x0E', b'\x0F', b'\x10', b'\x11', b'\x12',
    b'\x13', b'\x14', b'\x15', b'\x16', b'\x17', b'\x18', b'\x19', b'\x1A',
    b'\x1B', b'\x1C', b'\x1D', b'\x1E', b'\x1F', b'\x7F',
]


def remove_special_character(string):
    for special_character in SPECIAL_CHARACTER_BYTES_LS:
        string = string.replace(special_character.decode(), '')
    return string


def to_text(source):
    """ Generates a text value (an instance of text_type) from an arbitrary
    source.

    * False and None are converted to empty strings
    * text is passed through
    * bytes are decoded as UTF-8
    * rest is textified via the current version's relevant data model method
    """
    if source is None or source is False:
        return u''

    if isinstance(source, bytes):
        return source.decode('utf-8')
    # Dương : remove special character mac
    if isinstance(source, str):
        source = remove_special_character(source)
    if PY2:
        text_type = unicode
    else:
        text_type = str
    return text_type(source)


pycompat.to_text = to_text
