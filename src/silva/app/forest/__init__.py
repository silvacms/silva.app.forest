# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt
# this is package.

from silva.core import conf as silvaconf
from silva.core.conf.installer import DefaultInstaller
from zope.interface import Interface

silvaconf.extension_name("silva.app.forest")
silvaconf.extension_title("Silva Forest")
silvaconf.extension_depends(['Silva'])


class IExtension(Interface):
    """Silva Forest virtual hosting.
    """


class ForestInstaller(DefaultInstaller):
    """Install the service.
    """

    def install_custom(self, root):
        if 'service_forest' not in root.objectIds():
            factory = root.manage_addProduct['silva.app.forest']
            factory.manage_addForestService()


install = ForestInstaller("silva.app.forest", IExtension)
