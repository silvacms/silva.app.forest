# -*- coding: utf-8 -*-
# Copyright (c) 2013  Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from silva.core.views.site import WSGIVirtualSite
from infrae.wsgi.interfaces import IVirtualHosting
from silva.app.forest.interfaces import IForestHosting, IForestRequest


class ForestVirtualSite(WSGIVirtualSite):
    grok.context(IForestRequest)

    def get_top_level_url(self):
        plugin = self.request.get_plugin(IVirtualHosting)
        if IForestHosting.providedBy(plugin) and plugin.host is not None:
            top_levels = plugin.host.by_url.top()
            if len(top_levels) == 1:
                return top_levels[0].server_url
        return super(ForestVirtualSite, self).get_top_level_url()

    def get_top_level_path(self):
        plugin = self.request.get_plugin(IVirtualHosting)
        if IForestHosting.providedBy(plugin) and plugin.host is not None:
            top_levels = plugin.host.by_url.top()
            if len(top_levels) == 1:
                return '/' + '/'.join(top_levels[0].server_script)
        return super(ForestVirtualSite, self).get_top_level_path()
