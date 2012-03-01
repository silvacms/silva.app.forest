# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import logging

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Acquisition import aq_inner
import zExceptions

from five import grok
from zope.component import IFactory
from zope.component import queryUtility
from zope.interface import directlyProvides, alsoProvides, noLongerProvides
from zope.publisher.interfaces.browser import IBrowserSkinType
from infrae.wsgi.utils import traverse

from silva.app.forest import interfaces
from silva.app.forest import utils
from silva.core.services.base import SilvaService
from silva.core import conf as silvaconf
from silva.translations import translate as _
from zeam.form import silva as silvaforms

logger = logging.getLogger('infrae.rewriterule')


class ForestService(SilvaService):
    grok.implements(interfaces.IForestService)
    silvaconf.icon('service.png')
    meta_type = 'Silva Forest Service'
    default_service_identifier = 'service_forest'

    security = ClassSecurityInfo()
    manage_options = (
        {'label':'Settings', 'action':'manage_settings'},
        ) + SilvaService.manage_options

    _hosts = []
    _query_hosts = {}

    security.declareProtected(
        'View Management Screens', 'set_hosts')
    def set_hosts(self, hosts):
        query = {}
        root = self.getPhysicalRoot()
        for host in hosts:
            host.prepare(root)
            for url in [host.url, ] + list(host.aliases):
                key = utils.url2tuple(url)
                if key in query:
                    raise ValueError(u"Double entry for host %s." % url)
                query[key] = host

        # Save changes.
        self._hosts = hosts
        self._query_hosts = query

    security.declarePrivate('query')
    def query(self, key):
        return self._query_hosts.get(key)

    security.declareProtected(
        'View Management Screens', 'get_hosts')
    def get_hosts(self):
        return self._hosts

    hosts = property(get_hosts)

    def get_silva_path(self):
        return self.get_root().getPhysicalPath()[1:]

    security.declareProtected(
        'View Management Screens', 'is_active')
    def is_active(self):
        root = self.getPhysicalRoot()
        if interfaces.IForestApplication.providedBy(root):
            path = getattr(root, '__silva__', tuple())
            if path == self.get_silva_path():
                return True
        return False

    security.declareProtected(
        'View Management Screens', 'activate')
    def activate(self):
        root = self.getPhysicalRoot()
        if interfaces.IForestApplication.providedBy(root):
            raise ValueError(u"The feature is already activated for a Silva site.")
        setattr(root, '__silva__', self.get_silva_path())
        alsoProvides(root, interfaces.IForestApplication)

    security.declareProtected(
        'View Management Screens', 'deactivate')
    def deactivate(self):
        root = self.getPhysicalRoot()
        if not interfaces.IForestApplication.providedBy(root):
            raise ValueError(u"The feature is not activated.")
        path = getattr(root, '__silva__', tuple())
        if path != self.get_silva_path():
            raise ValueError(u"The feature is activated by an another Silva site.")
        delattr(root, '__silva__')
        noLongerProvides(root, interfaces.IForestApplication)


InitializeClass(ForestService)


class Rewrite(object):
    grok.implements(interfaces.IRewrite)

    def __init__(self, original, rewrite, skin):
        self.original = original
        self.rewrite = rewrite
        self.skin = skin
        self.path = []
        self.url = None

    def prepare(self, host, root):
        self.path = utils.path2tuple(self.rewrite)
        self.url = (host.url + self.original).rstrip('/')
        try:
            traverse(self.path, root)
        except zExceptions.BadRequest:
            raise ValueError(u"Invalid rewrite path %s" % self.rewrite)

    def apply(self, root, request):
        content = traverse(self.path, root, request)
        request['URL'] = self.url
        if self.skin:
            skin = queryUtility(IBrowserSkinType, name=self.skin)
            if skin is None:
                logger.error(
                    u"Missing skin '%s', please update your settings.",
                    self.skin)
            else:
                directlyProvides(request, skin)
        return content



grok.global_utility(
    Rewrite,
    provides=IFactory,
    name=interfaces.IRewrite.__identifier__,
    direct=True)


class VirtualHost(object):
    grok.implements(interfaces.IVirtualHost)

    def __init__(self, url, aliases, rewrites):
        self.url = url.rstrip('/')
        self.aliases = aliases
        self.rewrites = rewrites
        self.by_url = utils.TupleMap()
        self.by_path = utils.TupleMap()

    def prepare(self, root):
        base = utils.url2tuple(self.url)[3:]
        for rewrite in self.rewrites:
            rewrite.prepare(self, root)
            try:
                self.by_url.add(base + utils.path2tuple(rewrite.original), rewrite)
            except KeyError:
                raise ValueError(
                    u"Duplicate url entry for %s in %s" % (
                        rewrite.original, self.url))
            try:
                self.by_path.add(rewrite.path, rewrite)
            except KeyError:
                raise ValueError(
                    u"Duplicate path entry for %s in %s" % (
                        rewrite.rewrite, self.url))

    def query(self, key):
        return self.by_url.get(key, fallback=True)


grok.global_utility(
    VirtualHost,
    provides=IFactory,
    name=interfaces.IVirtualHost.__identifier__,
    direct=True)


class ForestManageSettings(silvaforms.ZMIComposedForm):
    grok.name('manage_settings')
    grok.context(ForestService)

    label = _(u"Forest Service configuration")
    description = _(u"Configure advanced virtual hosting in Silva.")


class ForestActivationSettings(silvaforms.ZMISubForm):
    """Active the virtual hosting.
    """
    grok.context(ForestService)
    grok.view(ForestManageSettings)
    grok.order(10)

    label = _(u"Activation")
    description = _(u"Activate or deactivate advanced virtual hosting for this Silva site.")

    @silvaforms.action(
        _(u"Activate"),
        available=lambda f: not f.context.is_active())
    def activate(self):
        try:
            self.context.activate()
        except ValueError, e:
            self.status = e.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS

    @silvaforms.action(
        _(u"Deactivate"),
        available=lambda f: f.context.is_active())
    def deactivate(self):
        try:
            self.context.deactivate()
        except ValueError, e:
            self.status = e.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS


class ForestVirtualHostSettings(silvaforms.ZMISubForm):
    """Configure the virtual hosts.
    """
    grok.context(ForestService)
    grok.view(ForestManageSettings)
    grok.order(20)

    label = _(u"Define the virtual hosts")
    fields = silvaforms.Fields(interfaces.IVirtualHostSettings)
    ignoreContent = False

    @silvaforms.action(_(u"Apply"))
    def apply(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        try:
            aq_inner(self.context).set_hosts(data['hosts'])
        except ValueError, e:
            self.status = e.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS
