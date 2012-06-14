# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from infrae.wsgi.interfaces import IVirtualHosting
from silva.app.forest.interfaces import IForestHosting
from silva.core.views import absoluteurl

from zExceptions import BadRequest


class SimpleURL(object):

    def _url(self, path, relative=False, preview=False):
        vhm = self.request.get_plugin(IVirtualHosting)
        if not IForestHosting.providedBy(vhm) or vhm.host is None:
            return self.request.physicalPathToURL(path)

        rule, index = vhm.host.by_path.get(path[1:], fallback=True)
        if rule is None:
            raise BadRequest(
                u"No virtual host is defined for %s" % self.context)

        path = list(path[index + 1:])
        if relative:
            return '/' + '/'.join(rule.server_script + path)
        return '/'.join([rule.url,] + path)


class AbsoluteURL(SimpleURL, absoluteurl.AbsoluteURL):
    pass

class BrainAbsoluteURL(SimpleURL, absoluteurl.BrainAbsoluteURL):
    pass


class ContentURL(object):

    def _url(self, path, relative=False, preview=False):
        vhm = self.request.get_plugin(IVirtualHosting)
        if not IForestHosting.providedBy(vhm) or vhm.host is None:
            # If the extension is not enabled, or we are not in a
            # rewriting situation, go up a level.
            return super(ContentURL, self)._url(
                path, preview=preview, relative=relative)

        rule, index = vhm.host.by_path.get(path[1:], fallback=True)
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
