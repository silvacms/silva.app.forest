# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok

from . import interfaces


class ForestEvent(object):
    grok.implements(interfaces.IForestEvent)

    def __init__(self, root, silva, service):
        self.root = root
        self.silva = silva
        self.service = service


class ForestActivatedEvent(ForestEvent):
    grok.implements(interfaces.IForestActivatedEvent)


class ForestWillBeActivatedEvent(ForestEvent):
    grok.implements(interfaces.IForestWillBeActivatedEvent)


class ForestWillBeDeactivatedEvent(ForestEvent):
    grok.implements(interfaces.IForestWillBeDeactivatedEvent)


class ForestDeactivatedEvent(ForestEvent):
    grok.implements(interfaces.IForestDeactivatedEvent)

