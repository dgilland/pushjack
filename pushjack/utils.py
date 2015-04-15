# -*- coding: utf-8 -*-
"""Utility functions.
"""

try:
    import simplejson as json
except ImportError:
    import json

from ._compat import range_ as range, string_types, iteritems


def chunk(seq, size):
    """Return generator that yields chunks of length `size` from `seq`."""
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def compact_dict(dct):
    return dict((key, value) for key, value in iteritems(dct)
                if value is not None)


def json_dumps(data):
    """Standardized json.dumps function with separators and sorted keys set."""
    return (json.dumps(data, separators=(',', ':'), sort_keys=True)
            .encode('utf8'))


def json_loads(string):
    """Standardized json.loads function."""
    if not isinstance(string, (string_types)):
        string = string.decode('utf8')
    return json.loads(str(string))
