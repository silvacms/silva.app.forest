# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope.interface.verify import verifyObject
from zope.component import getUtility
from Products.Silva.testing import TestRequest

from infrae.wsgi.interfaces import IVirtualHosting
from silva.core.views.interfaces import IVirtualSite

from ..interfaces import IForestService
from ..service import VirtualHost, Rewrite
from ..testing import FunctionalLayer


class VirtualSiteTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        # Add some test contents.
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addPublication('docs', 'Documentation')
        factory = self.root.docs.manage_addProduct['Silva']
        factory.manage_addFolder('user', 'User')
        factory.manage_addFolder('dev', 'Developer')
        factory.manage_addFolder('admin', 'Administrator')
        factory = self.root.docs.dev.manage_addProduct['Silva']
        factory.manage_addFolder('man', 'Man pages')

        # Activate the forest service
        service = getUtility(IForestService)
        service.set_hosts([
                VirtualHost(
                    'http://localhost/',
                    [],
                    [Rewrite('/', '/root/docs/dev', None),
                     Rewrite('/admin', '/root/docs/admin', None),
                     Rewrite('/site', '/root', None)]),
                VirtualHost(
                    'https://localhost/',
                    [],
                    [Rewrite('/', '/root'),
                     Rewrite('/admin', '/root/docs/admin', None)]),
                VirtualHost(
                    'https://complicated/',
                    [],
                    [Rewrite('/site', '/root'),
                     Rewrite('/admin', '/root/docs/admin', None)])])
        service.activate()

    def test_virtual_site_simple(self):
        """Test simple cases nothing special is set or done.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/man/edit',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)

        site = IVirtualSite(request)
        self.assertTrue(verifyObject(IVirtualSite, site))
        self.assertEqual(site.get_root_url(), 'http://localhost')
        self.assertEqual(site.get_root_path(), '/')
        self.assertEqual(site.get_top_level_url(), 'http://localhost')
        self.assertEqual(site.get_top_level_path(), '/')

    def test_virtual_site_top_level_is_not_root_at_top_level(self):
        """Test cases where the Silva root is not the highest URL you
        can get.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/man/edit',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)

        site = IVirtualSite(request)
        self.assertTrue(verifyObject(IVirtualSite, site))
        self.assertEqual(site.get_root_url(), 'http://localhost')
        self.assertEqual(site.get_root_path(), '/')
        self.assertEqual(site.get_top_level_url(), 'http://localhost')
        self.assertEqual(site.get_top_level_path(), '/')

    def test_virtual_site_top_level_is_not_root_at_root_level(self):
        """Test cases where the Silva root is not the highest URL you
        can get.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/site/edit',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)

        site = IVirtualSite(request)
        self.assertTrue(verifyObject(IVirtualSite, site))
        self.assertEqual(site.get_root_url(), 'http://localhost/site')
        self.assertEqual(site.get_root_path(), '/site')
        self.assertEqual(site.get_top_level_url(), 'http://localhost')
        self.assertEqual(site.get_top_level_path(), '/')

    def test_virtual_site_top_level_is_root(self):
        """Test cases where the Silva root is the highest URL you can
        get.
        """
        request = TestRequest(
            application=self.root,
            url='https://localhost/admin/edit',
            headers=[('X-VHM-Url', 'https://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)

        site = IVirtualSite(request)
        self.assertTrue(verifyObject(IVirtualSite, site))
        self.assertEqual(site.get_root_url(), 'https://localhost/admin')
        self.assertEqual(site.get_root_path(), '/admin')
        self.assertEqual(site.get_top_level_url(), 'https://localhost')
        self.assertEqual(site.get_top_level_path(), '/')

    def test_virtual_site_top_level_is_not_unique(self):
        """Test cases where the Silva root is the highest URL you can
        get.
        """
        # Sub case 1
        request = TestRequest(
            application=self.root,
            url='https://complicated/admin/edit',
            headers=[('X-VHM-Url', 'https://complicated')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)

        site = IVirtualSite(request)
        self.assertTrue(verifyObject(IVirtualSite, site))
        self.assertEqual(site.get_root_url(), 'https://complicated/admin')
        self.assertEqual(site.get_root_path(), '/admin')
        self.assertEqual(site.get_top_level_url(), 'https://complicated/admin')
        self.assertEqual(site.get_top_level_path(), '/admin')

        # Sub case 2
        request = TestRequest(
            application=self.root,
            url='https://complicated/site/edit',
            headers=[('X-VHM-Url', 'https://complicated')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)

        site = IVirtualSite(request)
        self.assertTrue(verifyObject(IVirtualSite, site))
        self.assertEqual(site.get_root_url(), 'https://complicated/site')
        self.assertEqual(site.get_root_path(), '/site')
        self.assertEqual(site.get_top_level_url(), 'https://complicated/site')
        self.assertEqual(site.get_top_level_path(), '/site')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(VirtualSiteTestCase))
    return suite
