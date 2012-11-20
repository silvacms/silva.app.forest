# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import urlparse

from Acquisition import aq_inner, aq_base, IAcquirer
from five import grok

from infrae.wsgi.interfaces import IPublicationAfterTraversal
from infrae.wsgi.interfaces import IRequest, IVirtualHosting
from infrae.wsgi.utils import traverse

from . import utils
from .interfaces import IForestApplication, IForestHosting
from .interfaces import IForestService

from zExceptions import BadRequest, NotFound


class VirtualHosting(grok.MultiAdapter):
    grok.adapts(IForestApplication, IRequest)
    grok.provides(IVirtualHosting)
    grok.implements(IForestHosting)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.root = None
        self.host = None
        try:
            self.service = self._load_service()
        except BadRequest:
            self.service = None

    def _load_service(self):
        return traverse(
            self.context.__silva__ + ('service_forest',), self.context)

    def rewrite_url(self, base_url, original_url):
        base = (None, None)
        base_host = None
        if base_url:
            # Look for a rewrite rule host matching base_url
            base = urlparse.urlparse(base_url)
            if self.service is not None and self.host is not None:
                base_host = self.service.query(
                    utils.url2tuple(base_url))
        original = urlparse.urlparse(original_url)
        if base_host is not None:
            # Look for full object path corresponding to the original url.
            original_path = utils.path2tuple(original.path)
            original_rule, original_index = self.host.query(original_path)
            if original_rule is None:
                raise BadRequest(
                    u"This original URL is not in the virtual host.")
            original_path = original_rule.path + original_path[original_index:]
            # Compute the url using base_host and the original path.
            base_rule, base_index = base_host.by_path.get(
                original_path, fallback=True)
            if base_rule is None:
                raise BadRequest(
                    u"This base URL is not in the virtual host.")
            return '/'.join((base_rule.url,) + original_path[base_index:])
        return urlparse.urlunparse(base[:2] + original[2:])

    def __call__(self, method, path):
        root = self.context
        url = self.request.environ.get('HTTP_X_VHM_URL')
        if self.service is None:
            self.service = self._load_service()
        if url:
            url_key = utils.url2tuple(url)
            assert IForestService.providedBy(self.service)
            self.host = self.service.query(url_key)
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


# @grok.subscribe(IPublicationAfterTraversal)
# def disable_acquisition_in_url(event):
#     content = event.content
#     if not (IAcquirer.providedBy(content) or hasattr(content, '__parent__')):
#         return

#     seen = set()
#     content = aq_inner(content)
#     while content is not None:
#         seen.add(id(aq_base(content)))
#         content = getattr(content, 'aq_parent',
#                           getattr(content, '__parent__', None))
#         if id(aq_base(content)) in seen:
#             raise NotFound()
