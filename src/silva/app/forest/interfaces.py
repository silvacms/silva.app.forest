# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from operator import attrgetter

from five import grok
from OFS.interfaces import IApplication
from zope.component import getUtilitiesFor
from zope.publisher.interfaces.browser import IBrowserSkinType
from zope.interface import Interface, Attribute
from zope import schema
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from zope.schema.interfaces import IContextSourceBinder
from infrae.wsgi.interfaces import IVirtualHosting
from infrae.wsgi.interfaces import IRequest

from silva.core.interfaces import ISilvaService
from silva.translations import translate as _
from silva.core.conf import schema as silvaschema


@grok.provider(IContextSourceBinder)
def skins(context):
    tokens = map(
        lambda (name, skin): SimpleTerm(value=name, token=name, title=name),
        getUtilitiesFor(IBrowserSkinType))
    tokens.sort(key=attrgetter('title'))
    tokens.insert(0, SimpleTerm(
            value=None, token='none', title=_('(No skin change)')))
    return SimpleVocabulary(tokens)


class IForestRequest(IRequest):
    """A request using the forest application.
    """


class IForestApplication(IApplication):
    """This is an Zope Application root that is linked to a Silva root.
    """

    __silva__ = Attribute(u"")


class IRewrite(Interface):
    original = schema.TextLine(
        title=_(u"Original URL path"),
        required=True)
    rewrite = schema.TextLine(
        title=_(u"Zope path"),
        required=True)
    skin =  schema.Choice(
        title=_(u"Skin to apply"),
        source=skins,
        required=False)
    skin_enforce =  schema.Bool(
        title=_(u"Force skin"),
        default=False,
        required=False)


class IVirtualHost(Interface):
    url = schema.URI(
        title=_(u"Virtual host URL"),
        required=True)
    aliases = schema.Set(
        title=_(u"Virtual host aliases"),
        value_type=schema.URI(required=True),
        required=False)
    rewrites = schema.Set(
        title=_(u"Rewrites rules"),
        value_type=schema.Object(schema=IRewrite),
        required=True)


class IVirtualHostSettings(Interface):
    hosts = schema.Set(
        title=_(u"Virtual hosts"),
        value_type=schema.Object(schema=IVirtualHost),
        required=True)


class IVirtualHostImportSettings(Interface):
    hosts_csv = silvaschema.Bytes(
        title=_(u"Import hosts"),
        description=_(u"Import host definition as a CSV file."),
        required=True)


class IForestService(ISilvaService, IVirtualHostSettings):
    """This stores the settings regarding rewrite rules.
    """


class IForestHosting(IVirtualHosting):
    """Our implements for the virtual hosting.
    """
    host = Attribute(u"Current used virtual host")


class IForestEvent(Interface):
    """ Base interface for forest events.
    """
    root = Attribute(u"Application root.")
    silva = Attribute(u"Silva root.")
    service = Attribute(u"Forest service.")


class IForestActivatedEvent(IForestEvent):
    """ Forest as been activated.
    """


class IForestWillBeActivatedEvent(IForestEvent):
    """ Forest will be activated.
    """


class IForestWillBeDeactivatedEvent(IForestEvent):
    """ Forest will be deactivated.
    """


class IForestDeactivatedEvent(IForestEvent):
    """ Forest has been deactivated.
    """
