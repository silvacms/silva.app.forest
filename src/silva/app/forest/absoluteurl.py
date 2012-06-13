# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.Five import BrowserView

from infrae.wsgi.interfaces import IVirtualHosting
from silva.app.forest.interfaces import IForestHosting
from silva.core.views.absoluteurl import AbsoluteURL
from zope.component import getMultiAdapter
from zope.interface import implements
from zope.traversing.browser.interfaces import IAbsoluteURL

from zExceptions import BadRequest


class ZopeForestURL(BrowserView):
    implements(IAbsoluteURL)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def url(self, relative=False):
        path = self.context.getPhysicalPath()
        vhm = self.request.get_plugin(IVirtualHosting)
        if not IForestHosting.providedBy(vhm) or vhm.host is None:
            return self.request.physicalPathToURL(path)

        rule, index = vhm.host.by_path.get(path[1:], fallback=True)
        if rule is None:
            raise BadRequest(
                u"No virtual host is defined for %s" % self.context)

        url = list(path[index + 1:])
        if relative:
            return '/'.join(rule.server_script + url)
        return rule.url + '/' + '/'.join(url)

    __call__ = __repr__ = __unicode__ = __str__ = url

    def breadcrumbs(self):
        return tuple()


class BrainForestURL(BrowserView):
    implements(IAbsoluteURL)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def url(self, relative=False):
        path = self.context.getPath()
        vhm = self.request.get_plugin(IVirtualHosting)
        if not IForestHosting.providedBy(vhm) or vhm.host is None:
            return self.request.physicalPathToURL(path)

        rule, index = vhm.host.by_path.get(path[1:], fallback=True)
        if rule is None:
            raise BadRequest(
                u"No virtual host is defined for %s" % self.context)

        url = list(path[index + 1:])
        if relative:
            return '/'.join(rule.server_script + url)
        return rule.url + '/' + '/'.join(url)

    __call__ = __repr__ = __unicode__ = __str__ = url

    def breadcrumbs(self):
        return tuple()


class ContentForestURL(AbsoluteURL):

    def url(self, preview=False, relative=False):
        path = self.context.getPhysicalPath()
        vhm = self.request.get_plugin(IVirtualHosting)
        if not IForestHosting.providedBy(vhm) or vhm.host is None:
            # If the extension is not enabled, or we are not in a
            # rewriting situation, go up a level.
            return super(ContentForestURL, self).url(
                preview=preview, relative=relative)

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
            return  '/'.join(rule.server_script + path)
        return rule.url + '/' + '/'.join(path)

    def is_virtual_root(self, path):
        vhm = self.request.get_plugin(IVirtualHosting)
        if not IForestHosting.providedBy(vhm) or vhm.host is None:
            # If the extension is not enabled, or we are not in a
            # rewriting situation, go up a level.
            return super(ContentForestURL, self).is_virtual_root(path)

        rule, index = vhm.host.by_path.get(path[1:])
        return rule is not None


class VersionForestURL(ContentForestURL):

    def title(self, preview=False):
        return self.context.get_short_title()


def absolute_url(self, relative=0):
    return getMultiAdapter(
        (self, self.REQUEST), IAbsoluteURL).url(relative=False)

def absolute_url_path(self):
    return getMultiAdapter(
        (self, self.REQUEST), IAbsoluteURL).url(relative=True)
