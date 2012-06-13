# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from zope.component import queryUtility
from zope.interface.verify import verifyObject
from infrae.wsgi.testing import TestRequest
from infrae.wsgi.interfaces import IVirtualHosting

from ..interfaces import IForestService, IVirtualHost, IRewrite
from ..interfaces import IForestHosting
from ..service import VirtualHost, Rewrite
from ..testing import FunctionalLayer
from ..utils import url2tuple


class ServiceTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()

    def test_service(self):
        service = queryUtility(IForestService)
        self.assertNotEqual(service, None)
        self.assertTrue(verifyObject(IForestService, service))
        self.assertFalse(service.is_active())
        self.assertEqual(service.get_hosts(), [])
        service.set_hosts([])
        self.assertEqual(service.get_hosts(), [])

    def test_activation(self):
        service = queryUtility(IForestService)
        service.activate()
        self.assertTrue(service.is_active())

        request = TestRequest(application=self.root)
        plugin = request.query_plugin(request.application, IVirtualHosting)
        self.assertTrue(verifyObject(IForestHosting, plugin))

        # You cannot activate the service twice.
        with self.assertRaises(ValueError):
            service.activate()

        self.assertTrue(service.is_active())
        service.deactivate()
        self.assertFalse(service.is_active())

        # The service is not active.
        with self.assertRaises(ValueError):
            service.deactivate()

    def test_host_root(self):
        """Set an host that is the root of the URL.
        """
        service = queryUtility(IForestService)

        hosts = [
            VirtualHost(
                'http://infrae.com/',
                [],
                [Rewrite('/', '/root', None)])]

        service.set_hosts(hosts)
        self.assertEqual(service.get_hosts(), hosts)
        host = hosts[0]
        self.assertTrue(verifyObject(IVirtualHost, host))
        self.assertEqual(host.url, 'http://infrae.com')
        self.assertEqual(host.aliases, [])
        self.assertEqual(len(host.rewrites), 1)
        rewrite = host.rewrites[0]
        self.assertTrue(verifyObject(IRewrite, rewrite))
        self.assertEqual(rewrite.original, '/')
        self.assertEqual(rewrite.rewrite, '/root')
        self.assertEqual(rewrite.url, 'http://infrae.com')
        self.assertEqual(rewrite.server_url, 'http://infrae.com')
        self.assertEqual(rewrite.server_script, [])

        query_host = service.query(url2tuple('http://infrae.com'))
        self.assertIs(query_host, host)

    def test_host_sub(self):
        """Create an host that is a sub-path to a site.
        """
        service = queryUtility(IForestService)

        hosts = [
            VirtualHost(
                'http://infrae.com/docs',
                [],
                [Rewrite('/silva', '/root', None)])]

        service.set_hosts(hosts)
        self.assertEqual(service.get_hosts(), hosts)
        host = hosts[0]
        self.assertTrue(verifyObject(IVirtualHost, host))
        self.assertEqual(host.url, 'http://infrae.com/docs')
        self.assertEqual(host.aliases, [])
        self.assertEqual(len(host.rewrites), 1)
        rewrite = host.rewrites[0]
        self.assertTrue(verifyObject(IRewrite, rewrite))
        self.assertEqual(rewrite.original, '/silva')
        self.assertEqual(rewrite.rewrite, '/root')
        self.assertEqual(rewrite.url, 'http://infrae.com/docs/silva')
        self.assertEqual(rewrite.server_url, 'http://infrae.com')
        self.assertEqual(rewrite.server_script, ['docs', 'silva'])

        query_host = service.query(url2tuple('http://infrae.com'))
        self.assertIs(query_host, None)
        query_host = service.query(url2tuple('http://infrae.com/docs'))
        self.assertIs(query_host, host)

    def test_host_multiple_rewrite(self):
        """Set an host that contains multiple rewrites.
        """
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('docs', 'Docs')
        factory = self.root.docs.manage_addProduct['Silva']
        factory.manage_addFolder('admin', 'Administration')
        factory.manage_addFolder('user', 'User')
        factory.manage_addFolder('dev', 'Developers')

        service = queryUtility(IForestService)

        hosts = [
            VirtualHost(
                'http://infrae.com/',
                [],
                [Rewrite('/', '/root', None),
                 Rewrite('/admin', '/root/docs/admin', None),
                 Rewrite('/hidden/advanced', '/root/docs/dev', None)])]

        service.set_hosts(hosts)
        self.assertEqual(service.get_hosts(), hosts)
        host = hosts[0]
        self.assertTrue(verifyObject(IVirtualHost, host))
        self.assertEqual(host.url, 'http://infrae.com')
        self.assertEqual(host.aliases, [])
        self.assertEqual(len(host.rewrites), 3)
        rewrite = host.rewrites[0]
        self.assertTrue(verifyObject(IRewrite, rewrite))
        self.assertEqual(rewrite.original, '/')
        self.assertEqual(rewrite.rewrite, '/root')
        self.assertEqual(rewrite.url, 'http://infrae.com')
        self.assertEqual(rewrite.server_url, 'http://infrae.com')
        self.assertEqual(rewrite.server_script, [])
        rewrite = host.rewrites[1]
        self.assertTrue(verifyObject(IRewrite, rewrite))
        self.assertEqual(rewrite.original, '/admin')
        self.assertEqual(rewrite.rewrite, '/root/docs/admin')
        self.assertEqual(rewrite.url, 'http://infrae.com/admin')
        self.assertEqual(rewrite.server_url, 'http://infrae.com')
        self.assertEqual(rewrite.server_script, ['admin'])
        rewrite = host.rewrites[2]
        self.assertTrue(verifyObject(IRewrite, rewrite))
        self.assertEqual(rewrite.original, '/hidden/advanced')
        self.assertEqual(rewrite.rewrite, '/root/docs/dev')
        self.assertEqual(rewrite.url, 'http://infrae.com/hidden/advanced')
        self.assertEqual(rewrite.server_url, 'http://infrae.com')
        self.assertEqual(rewrite.server_script, ['hidden', 'advanced'])

        # test query
        query_host = service.query(url2tuple('http://infrae.com'))
        self.assertIs(query_host, host)

    def test_host_duplicate(self):
        """Try to create a duplicated host.
        """
        service = queryUtility(IForestService)

        hosts = [
            VirtualHost(
                'http://infrae.com/docs',
                [],
                [Rewrite('/silva', '/root', None)]),
            VirtualHost(
                'http://infrae.com/docs',
                [],
                [Rewrite('/silva', '/root', None)])]

        with self.assertRaises(ValueError):
            service.set_hosts(hosts)

    def test_host_invalid_path(self):
        """Try to create a duplicated host.
        """
        service = queryUtility(IForestService)

        hosts = [
            VirtualHost(
                'http://infrae.com',
                [],
                [Rewrite('/', '/silva', None)])]

        with self.assertRaises(ValueError):
            service.set_hosts(hosts)

    def test_host_duplicate_path(self):
        """Try to create a duplicated host.
        """
        service = queryUtility(IForestService)

        hosts = [
            VirtualHost(
                'http://infrae.com',
                [],
                [Rewrite('/', '/root', None),
                 Rewrite('/docs', '/root', None)])]

        with self.assertRaises(ValueError):
            service.set_hosts(hosts)

    def test_host_duplicate_url(self):
        """Try to create a duplicated url.
        """
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('folder', 'Folder')

        service = queryUtility(IForestService)

        hosts = [
            VirtualHost(
                'http://infrae.com',
                [],
                [Rewrite('/', '/root', None),
                 Rewrite('/', '/root/folder', None)])]

        with self.assertRaises(ValueError):
            service.set_hosts(hosts)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ServiceTestCase))
    return suite
