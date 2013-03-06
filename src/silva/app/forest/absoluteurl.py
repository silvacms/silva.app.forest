# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import logging

from infrae.wsgi.interfaces import IVirtualHosting
from silva.app.forest.interfaces import IForestHosting
from silva.app.forest.utils import url2tuple
from silva.core.views import absoluteurl

from zExceptions import BadRequest

logger = logging.getLogger('silva.app.forest')


class SimpleURL(object):

    def _url(self, path, preview=False, relative=False, host=None):
        plugin = self.request.get_plugin(IVirtualHosting)
        if not IForestHosting.providedBy(plugin):
            return super(SimpleURL, self)._url(path, preview, relative, host)

        virtual_host = plugin.host
        if host is not None:
            virtual_host = plugin.service.query(url2tuple(host))
        if virtual_host is None:
            return super(SimpleURL, self)._url(path, preview, relative, host)

        rule, index = virtual_host.by_path.get(path[1:], fallback=True)
        if rule is None:
            logger.error(
                u"No virtual host defined to compute URL for path %s.",
                '/'.join(path))
            # Broken fallback that will generate a relative URL to
            # prevent breaking the ZMI.
            return '/'.join(path)

        path = list(path[index + 1:])
        if relative:
            return '/' + '/'.join(rule.server_script + path)
        return '/'.join([rule.url,] + path)


class AbsoluteURL(SimpleURL, absoluteurl.AbsoluteURL):
    pass


class BrainAbsoluteURL(SimpleURL, absoluteurl.BrainAbsoluteURL):
    pass


class ContentURL(object):

    def _virtual_root(self, content):
        vhm = self.request.get_plugin(IVirtualHosting)
        return vhm.root == content

    def _url(self, path, preview=False, relative=False, host=None):
        plugin = self.request.get_plugin(IVirtualHosting)
        if not IForestHosting.providedBy(plugin):
            return super(ContentURL, self)._url(path, preview, relative, host)

        virtual_host = plugin.host
        if host is not None:
            virtual_host = plugin.service.query(url2tuple(host))
        if virtual_host is None:
            return super(ContentURL, self)._url(path, preview, relative, host)

        rule, index = virtual_host.by_path.get(path[1:], fallback=True)
        if rule is None:
            raise BadRequest(
                u"No virtual host is defined for %s" % self.context)
        path = list(path[index + 1:])

        if preview is True:
            preview_position = max(
                len(self.context.get_root().getPhysicalPath()) - (index + 1), 0)
            path.insert(preview_position, '++preview++')

        if relative:
            return '/' + '/'.join(rule.server_script + path)
        return '/'.join([rule.url,] + path)


class ContentAbsoluteURL(ContentURL, absoluteurl.ContentAbsoluteURL):
    pass


class VersionAbsoluteURL(ContentURL, absoluteurl.VersionAbsoluteURL):
    pass


class ErrorAbsoluteURL(ContentURL, absoluteurl.ErrorAbsoluteURL):
    pass
