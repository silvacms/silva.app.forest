# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

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

from silva.core.interfaces import ISilvaService
from silva.translations import translate as _


@grok.provider(IContextSourceBinder)
def skins(context):
    tokens = map(
        lambda (name, skin): SimpleTerm(value=name, token=name, title=name),
        getUtilitiesFor(IBrowserSkinType))
    tokens.sort(key=attrgetter('title'))
    tokens.insert(0, SimpleTerm(
            value=None, token='none', title=_('(No skin change)')))
    return SimpleVocabulary(tokens)


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


class IForestService(ISilvaService, IVirtualHostSettings):
    """This stores the settings regarding rewrite rules.
    """


class IForestHosting(IVirtualHosting):
    """Our implements for the virtual hosting.
    """
    host = Attribute(u"Current used virtual host")
