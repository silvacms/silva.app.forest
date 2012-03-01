# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$


import urlparse
from infrae.wsgi.utils import split_path_info

_marker = object()

def path2tuple(path):
    return tuple(split_path_info(path))

def url2tuple(url, strict=False):
    info = urlparse.urlparse(url)
    if strict and info[4] or info[5]:
        raise ValueError(u'Invalid URL %s' % url)
    scheme = info[0] or 'http'
    hostname = info[1]
    if ':' in hostname:
        hostname, port = hostname.split(':', 1)
    else:
        if scheme == 'https':
            port = '443'
        else:
            port = '80'
    return (scheme, hostname, port, ) + path2tuple(info[2])


class TupleMap(object):

    def __init__(self):
        self.clear()

    def clear(self):
        self._store = {}
        self._len = 0

    def add(self, key, value):
        store = self._store
        for piece in key:
            store = store.setdefault(piece, {})
        if None in store:
            # There is already a value in the store.
            raise KeyError(key)
        store[None] = value
        self._len += 1
        return value

    def get(self, key, default=None, fallback=False):
        store = self._store
        default_index = 0

        for index, piece in enumerate(key):
            following = store.get(piece)

            if fallback:
                # Update default if fallback is on
                default_fallback = store.get(None)
                if default_fallback is not None:
                    default = default_fallback
                    default_index = index

            if following is None:
                # Not found, return default.
                return default, default_index

            store = following

        # Look for value or return default.
        value = store.get(None)
        if value is not None:
            return value, index + 1
        return default, default_index

    def list(self):
        result = []

        def walk(level):
            for piece, value in level.iteritems():
                if piece is None:
                    result.append(value)
                else:
                    walk(value)

        walk(self._store)
        return result

    def __getitem__(self, key):
        value = self.get(key, _marker)[0]
        if value is _marker:
            raise KeyError(key)
        return value

    def __len__(self):
        return self._len
