# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$


from silva.core.views.absoluteurl import AbsoluteURL
from infrae.wsgi.interfaces import IVirtualHosting
from silva.app.forest.interfaces import IForestHosting

from zExceptions import BadRequest


class ForestURL(AbsoluteURL):

    def url(self, preview=False):
        vhm = self.request.get_plugin(IVirtualHosting)
        if not IForestHosting.providedBy(vhm) or vhm.host is None:
            # If the extension is not enabled, or we are not in a
            # rewriting situation, go up a level.
            return super(ForestURL, self).url(preview=preview)

        path = self.context.getPhysicalPath()[1:]
        rule, index = vhm.host.by_path.get(path, fallback=True)
        if rule is None:
            raise BadRequest(u"No virtual host is defined for %s" % self.context)

        path = list(path[index:])

        if preview is True:
            preview_position = max(
                len(self.context.get_root().getPhysicalPath()) - index,
                0)
            path.insert(preview_position, self._preview_ns)

        return rule.url + '/' + '/'.join(path)
