# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt


import unittest

from zope.component import getUtility
from Products.Silva.testing import TestRequest

from infrae.wsgi.interfaces import IVirtualHosting

from ..interfaces import IForestService
from ..service import VirtualHost, Rewrite
from ..testing import FunctionalLayer


class RewriteURLTestCase(unittest.TestCase):
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
                    [Rewrite('/', '/root')])])
        service.activate()

    def test_rewrite_url_no_change(self):
        """Test simple cases where rewritting a URL should not changes
        its URL path.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/man/edit',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)

        self.assertEqual(
            plugin.rewrite_url(None, 'http://localhost/man/edit'),
            '/man/edit')
        self.assertEqual(
            plugin.rewrite_url(
                'http://localhost',
                'http://localhost/man/edit'),
            'http://localhost/man/edit')
        self.assertEqual(
            plugin.rewrite_url(
                'http://localhost',
                'http://localhost/site/docs/users/edit'),
            'http://localhost/site/docs/users/edit')

    def test_rewrite_url_change_path_multiple_to_one(self):
        """Test cases where rewritting a URL should change its URL path.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/man/edit',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)

        self.assertEqual(
            plugin.rewrite_url(
                'https://localhost',
                'http://localhost/man/edit'),
            'https://localhost/docs/dev/man/edit')
        self.assertEqual(
            plugin.rewrite_url(
                'https://localhost',
                'http://localhost/admin/edit'),
            'https://localhost/docs/admin/edit')
        self.assertEqual(
            plugin.rewrite_url(
                'https://localhost',
                'http://localhost/site/docs/users/edit'),
            'https://localhost/docs/users/edit')

    def test_rewrite_url_change_path_one_to_multiple(self):
        """Test cases where rewritting a URL should change its URL path.
        """
        request = TestRequest(
            application=self.root,
            url='https://localhost/docs/admin/edit',
            headers=[('X-VHM-Url', 'https://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)

        self.assertEqual(
            plugin.rewrite_url(
                'http://localhost',
                'https://localhost/docs/dev/man/edit'),
            'http://localhost/man/edit')
        self.assertEqual(
            plugin.rewrite_url(
                'http://localhost',
                'https://localhost/docs/admin/edit'),
            'http://localhost/admin/edit')
        self.assertEqual(
            plugin.rewrite_url(
                'http://localhost',
                'https://localhost/docs/users/edit'),
            'http://localhost/site/docs/users/edit')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RewriteURLTestCase))
    return suite
