# -*- coding: utf-8 -*-
"""Utility functions.
"""

try:
    import simplejson as json
except ImportError:
    import json

from ._compat import range_ as range


def chunk(seq, size):
    """Return generator that yields chunks of length `size` from `seq`."""
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def json_dumps(data):
    """Standardized json.dumps function with separators and sorted keys set."""
    return (json.dumps(data, separators=(',', ':'), sort_keys=True)
            .encode('utf8'))
