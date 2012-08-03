# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import csv
import logging
import urlparse
import collections

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Acquisition import aq_inner
import zExceptions

from five import grok
from zope.component import IFactory
from zope.component import queryUtility
from zope.interface import alsoProvides, noLongerProvides
from zope.publisher.interfaces.browser import IBrowserSkinType
from infrae.wsgi.utils import traverse, split_path_info

from silva.app.forest import interfaces
from silva.app.forest import utils
from silva.core import conf as silvaconf
from silva.core.interfaces import ISilvaObject
from silva.core.layout.interfaces import ISkinLookup
from silva.core.layout.traverser import SET_SKIN_ALLOWED_FLAG
from silva.core.layout.traverser import applySkinButKeepSome
from silva.core.services.base import SilvaService
from silva.translations import translate as _
from zeam.form import silva as silvaforms

logger = logging.getLogger('infrae.rewriterule')

str_from = collections.namedtuple(
    'str_from',
    ['url', 'original', 'rewrite', 'skin', 'skin_enforce'])

def to_str(value):
    if isinstance(value, unicode):
        return value.encode('utf-8')
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        if value:
            return 'on'
        return 'off'
    if value is None:
        return ''
    raise NotImplementedError()


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
        'View Management Screens', 'export_csv')
    def export_csv(self, stream):
        writer = csv.writer(stream)
        for host in self._hosts:
            for rewrite in host.rewrites:
                writer.writerow(map(
                        to_str, [host.url,
                                 rewrite.original,
                                 rewrite.rewrite,
                                 rewrite.skin,
                                 rewrite.skin_enforce]))

    security.declareProtected(
        'View Management Screens', 'import_csv')
    def import_csv(self, stream):
        reader = csv.reader(stream)
        hosts = []
        host = None
        for number, line in enumerate(reader):
            if len(line) != 5:
                raise ValueError(
                    u"Invalid number of options at line %d." % number)
            data = str_from(*line)
            if host is None or data.url != host.url:
                if host is not None:
                    hosts.append(host)
                host = VirtualHost(data.url, [], [])
            host.rewrites.append(
                Rewrite(
                    data.original,
                    data.rewrite,
                    data.skin or None,
                    data.skin_enforce == 'on'))
        if host is not None:
            hosts.append(host)
        self.set_hosts(hosts)

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
            raise ValueError(
                _(u"The feature is already activated for a Silva site."))
        setattr(root, '__silva__', self.get_silva_path())
        alsoProvides(root, interfaces.IForestApplication)

    security.declareProtected(
        'View Management Screens', 'deactivate')
    def deactivate(self):
        root = self.getPhysicalRoot()
        if not interfaces.IForestApplication.providedBy(root):
            raise ValueError(
                _(u"The feature is not activated."))
        path = getattr(root, '__silva__', tuple())
        if path != self.get_silva_path():
            raise ValueError(
                _(u"The feature is activated by an another Silva site."))
        delattr(root, '__silva__')
        noLongerProvides(root, interfaces.IForestApplication)


InitializeClass(ForestService)


def update_hostname(url, target):
    # replace the host part.
    original_parts = urlparse.urlparse(url)
    target_parts = urlparse.urlparse(target)
    return urlparse.urlunparse(
        original_parts[:2] + target_parts[2:])


class Rewrite(object):
    grok.implements(interfaces.IRewrite)

    def __init__(self, original, rewrite, skin=None, skin_enforce=True):
        self.original = str(original)
        self.rewrite = str(rewrite)
        self.skin = skin
        self.skin_enforce = skin_enforce
        self.path = []
        self.url = None
        self.server_url = None
        self.server_script = None

    def prepare(self, host, root):
        self.path = utils.path2tuple(self.rewrite)
        self.url = (host.url + self.original).rstrip('/')
        url_parts = urlparse.urlparse(self.url)
        self.server_url = urlparse.urlunparse(url_parts[:2] + ('',) * 4)
        self.server_script = split_path_info(url_parts[2])
        try:
            traverse(self.path, root)
        except zExceptions.BadRequest:
            raise ValueError(u"Invalid rewrite path %s" % self.rewrite)

    def apply(self, root, request):
        content = traverse(self.path, root, request)
        request['URL'] = self.url
        request['ACTUAL_URL'] = self.server_url + urlparse.urlunparse(
            ('', '') + urlparse.urlparse(request['ACTUAL_URL'])[2:])
        request['SERVER_URL'] = str(self.server_url)
        request._script = list(self.server_script)
        request._resetURLS()
        if self.skin:
            # Apply hardcoded skin
            skin = queryUtility(IBrowserSkinType, name=self.skin)
            if skin is None:
                logger.error(
                    u"Missing skin '%s', please update your settings.",
                    self.skin)
            else:
                applySkinButKeepSome(request, skin)
                if self.skin_enforce:
                    request[SET_SKIN_ALLOWED_FLAG] = False
        else:
            # Fallback on the default Silva skin
            if ISilvaObject.providedBy(content):
                publication = content.get_publication()
                skin_lookup = ISkinLookup(publication, None)
                if skin_lookup is not None:
                    skin = skin_lookup.get_skin(request)
                    if skin is not None:
                        # We found a skin to apply
                        applySkinButKeepSome(request, skin)

        return content



grok.global_utility(
    Rewrite,
    provides=IFactory,
    name=interfaces.IRewrite.__identifier__,
    direct=True)


class VirtualHost(object):
    grok.implements(interfaces.IVirtualHost)

    def __init__(self, url, aliases, rewrites):
        self.url = str(url).rstrip('/')
        self.aliases = aliases
        self.rewrites = rewrites
        self.by_url = utils.TupleMap()
        self.by_path = utils.TupleMap()

    def prepare(self, root):
        base = utils.url2tuple(self.url)[3:]
        for rewrite in self.rewrites:
            rewrite.prepare(self, root)
            try:
                self.by_url.add(
                    base + utils.path2tuple(rewrite.original),
                    rewrite)
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
    description = _(u"Activate or deactivate advanced virtual hosting "
                    u"for this Silva site.")

    @silvaforms.action(
        _(u"Activate"),
        available=lambda f: not f.context.is_active())
    def activate(self):
        try:
            self.context.activate()
        except ValueError as error:
            self.status = error.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS

    @silvaforms.action(
        _(u"Deactivate"),
        available=lambda f: f.context.is_active())
    def deactivate(self):
        try:
            self.context.deactivate()
        except ValueError as error:
            self.status = error.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS


class ForestVirtualHostSettings(silvaforms.ZMISubForm):
    """Configure the virtual hosts.
    """
    grok.context(ForestService)
    grok.view(ForestManageSettings)
    grok.order(20)

    label = _(u"Define the virtual hosts")
    description = _(
        u"Define the virtual hosts usuable by the 'X-VHM-Url' HTTP header, "
        u"and the list of URL rewriting that will happen inside this virtual "
        u"host. You have the possibility to set (and enforce) a specific skin "
        u"for a given rewriting rule.")
    fields = silvaforms.Fields(interfaces.IVirtualHostSettings)
    ignoreContent = False

    @silvaforms.action(_(u"Apply"))
    def apply(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        try:
            aq_inner(self.context).set_hosts(data['hosts'])
        except ValueError as error:
            self.status = error.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS


class ForestVirtualHostExportSettings(silvaforms.ZMISubForm):
    """Configure the virtual hosts.
    """
    grok.context(ForestService)
    grok.view(ForestManageSettings)
    grok.order(30)

    label = _(u'Import or export the virtual hosts')
    fields = silvaforms.Fields(interfaces.IVirtualHostImportSettings)
    ignoreRequest=True
    ignoreContent=True

    @silvaforms.action(_(u"Import"))
    def import_hosts(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        try:
            aq_inner(self.context).import_csv(data['hosts_csv'])
        except ValueError as error:
            self.status = error.args[0]
            return silvaforms.FAILURE
        self.status = _(u"Virtual hosts imported.")
        return silvaforms.SUCCESS

    @silvaforms.action(_(u"Export"))
    def export_hosts(self):
        self.redirect(self.url('export.csv'))


class ForestVirtualHostExport(grok.View):
    grok.context(ForestService)
    grok.require('zope2.ViewManagementScreens')
    grok.name('export.csv')

    def render(self):
        self.response.setHeader('Content-Type', 'text/csv;charset=utf-8')
        return self.context.export_csv(self.response)

