# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import urlparse

from five import grok

from infrae.wsgi.interfaces import IRequest, IVirtualHosting
from infrae.wsgi.utils import traverse
from silva.app.forest.interfaces import IForestApplication
from silva.app.forest.interfaces import IForestHosting
from silva.app.forest import utils

from zExceptions import BadRequest


class VirtualHosting(grok.MultiAdapter):
    grok.adapts(IForestApplication, IRequest)
    grok.provides(IVirtualHosting)
    grok.implements(IForestHosting)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.root = None
        self.host = None

    def rewrite_url(self, base_url, original_url):
        base = (None, None)
        if base_url:
            base = urlparse.urlparse(base_url)[:2]
        return urlparse.urlunparse(
            base + urlparse.urlparse(original_url)[2:])

    def __call__(self, method, path):
        root = self.context
        url = self.request.environ.get('HTTP_X_VHM_URL')
        if url:
            url_key = utils.url2tuple(url)
            service = traverse(root.__silva__ + ('service_forest',), root)
            self.host = service.query(url_key)
            if self.host is not None:
                path_key = tuple(reversed(path))
                rule, index = self.host.query(path_key)
                if rule is not None:
                    root = rule.apply(root, self.request)
                    self.root = root
                    if index:
                        path = path[:-index]
                else:
                    raise BadRequest(u"This URL is not in the virtual host.")

        return root, method, path
