# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import io
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

        # Test host
        query_host = service.query(url2tuple('http://infrae.com'))
        self.assertIsNot(query_host, None)
        self.assertEqual(query_host.url, 'http://infrae.com')
        # Test rule
        query_rule, index = query_host.query(('contact',))
        self.assertEqual(index, 0)
        self.assertIsNot(query_rule, None)
        self.assertEqual(query_rule.url, 'http://infrae.com')
        self.assertEqual(query_rule.path, ('root',))
        self.assertEqual(query_rule.server_url, 'http://infrae.com')
        self.assertEqual(query_rule.server_script, [])

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

        # Test host
        query_host = service.query(url2tuple('http://infrae.com'))
        self.assertIs(query_host, None)
        query_host = service.query(url2tuple('http://infrae.com/docs'))
        self.assertIsNot(query_host, None)
        self.assertEqual(query_host.url, 'http://infrae.com/docs')
        # Test rule
        query_rule, index = query_host.query(('docs', 'silva', 'index'))
        self.assertIsNot(query_rule, None)
        self.assertEqual(index, 2)
        self.assertEqual(query_rule.url, 'http://infrae.com/docs/silva')
        self.assertEqual(query_rule.path, ('root',))
        self.assertEqual(query_rule.server_url, 'http://infrae.com')
        self.assertEqual(query_rule.server_script, ['docs', 'silva'])

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
        self.assertEqual(rewrite.skin, None)
        self.assertEqual(rewrite.skin_enforce, True)
        rewrite = host.rewrites[1]
        self.assertTrue(verifyObject(IRewrite, rewrite))
        self.assertEqual(rewrite.original, '/admin')
        self.assertEqual(rewrite.rewrite, '/root/docs/admin')
        self.assertEqual(rewrite.skin, None)
        self.assertEqual(rewrite.skin_enforce, True)
        rewrite = host.rewrites[2]
        self.assertTrue(verifyObject(IRewrite, rewrite))
        self.assertEqual(rewrite.original, '/hidden/advanced')
        self.assertEqual(rewrite.rewrite, '/root/docs/dev')
        self.assertEqual(rewrite.skin, None)
        self.assertEqual(rewrite.skin_enforce, True)

        # Test query
        query_host = service.query(url2tuple('http://infrae.com'))
        self.assertIsNot(query_host, None)
        self.assertEqual(query_host.url, 'http://infrae.com')

        # Test rewrites
        query_rule, index = query_host.query(('index',))
        self.assertIsNot(query_rule, None)
        self.assertEqual(index, 0)
        self.assertEqual(query_rule.url, 'http://infrae.com')
        self.assertEqual(query_rule.path, ('root',))
        self.assertEqual(query_rule.server_url, 'http://infrae.com')
        self.assertEqual(query_rule.server_script, [])

        query_rule, index = query_host.query(('admin', 'index',))
        self.assertIsNot(query_rule, None)
        self.assertEqual(index, 1)
        self.assertEqual(query_rule.url, 'http://infrae.com/admin')
        self.assertEqual(query_rule.path, ('root', 'docs', 'admin'))
        self.assertEqual(query_rule.server_url, 'http://infrae.com')
        self.assertEqual(query_rule.server_script, ['admin'])

        query_rule, index = query_host.query(('hidden', 'advanced',))
        self.assertIsNot(query_rule, None)
        self.assertEqual(index, 2)
        self.assertEqual(query_rule.url, 'http://infrae.com/hidden/advanced')
        self.assertEqual(query_rule.path, ('root', 'docs', 'dev'))
        self.assertEqual(query_rule.server_url, 'http://infrae.com')
        self.assertEqual(query_rule.server_script, ['hidden', 'advanced'])

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


class ServiceImportExportTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('docs', 'Docs')
        factory = self.root.docs.manage_addProduct['Silva']
        factory.manage_addFolder('admin', 'Administration')
        factory.manage_addFolder('user', 'User')
        factory.manage_addFolder('dev', 'Developers')

    def test_export_csv(self):
        """Try to export a configuration as a CSV file.
        """
        service = queryUtility(IForestService)
        hosts = [
            VirtualHost(
                'http://infrae.com/docs',
                [],
                [Rewrite('/', '/root', None),
                 Rewrite('/admin', '/root/docs/admin', None),
                 Rewrite('/hidden/advanced', '/root/docs/dev', None)]),
            VirtualHost(
                'http://infrae.com',
                [],
                [Rewrite('/silva', '/root', None)])]
        stream = io.BytesIO()

        service.set_hosts(hosts)
        service.export_csv(stream)
        self.assertMultiLineEqual(
            stream.getvalue().replace('\r\n', '\n'),
            """http://infrae.com/docs,/,/root,,on
http://infrae.com/docs,/admin,/root/docs/admin,,on
http://infrae.com/docs,/hidden/advanced,/root/docs/dev,,on
http://infrae.com,/silva,/root,,on
""")

    def test_import_csv(self):
        """Test importing the host definition from a CSV file.
        """
        service = queryUtility(IForestService)
        self.assertEqual(service.get_hosts(), [])

        with self.layer.open_fixture('valid_hosts.csv') as hosts:
            service.import_csv(hosts)

        hosts = service.get_hosts()
        self.assertEqual(len(hosts), 2)
        host = hosts[0]
        self.assertTrue(verifyObject(IVirtualHost, host))
        self.assertEqual(host.url, 'http://infrae.com/docs')
        self.assertEqual(host.aliases, [])
        self.assertEqual(len(host.rewrites), 3)
        rewrite = host.rewrites[0]
        self.assertTrue(verifyObject(IRewrite, rewrite))
        self.assertEqual(rewrite.original, '/')
        self.assertEqual(rewrite.rewrite, '/root')
        self.assertEqual(rewrite.skin, None)
        self.assertEqual(rewrite.skin_enforce, True)
        rewrite = host.rewrites[1]
        self.assertTrue(verifyObject(IRewrite, rewrite))
        self.assertEqual(rewrite.original, '/admin')
        self.assertEqual(rewrite.rewrite, '/root/docs/admin')
        self.assertEqual(rewrite.skin, None)
        self.assertEqual(rewrite.skin_enforce, True)
        rewrite = host.rewrites[2]
        self.assertTrue(verifyObject(IRewrite, rewrite))
        self.assertEqual(rewrite.original, '/hidden/advanced')
        self.assertEqual(rewrite.rewrite, '/root/docs/dev')
        self.assertEqual(rewrite.skin, None)
        self.assertEqual(rewrite.skin_enforce, True)
        host = hosts[1]
        self.assertTrue(verifyObject(IVirtualHost, host))
        self.assertEqual(host.url, 'http://infrae.com')
        self.assertEqual(host.aliases, [])
        self.assertEqual(len(host.rewrites), 1)
        rewrite = host.rewrites[0]
        self.assertTrue(verifyObject(IRewrite, rewrite))
        self.assertEqual(rewrite.original, '/silva')
        self.assertEqual(rewrite.rewrite, '/root')
        self.assertEqual(rewrite.skin, 'Standard Issue')
        self.assertEqual(rewrite.skin_enforce, False)

        # Test query
        query_host = service.query(url2tuple('http://infrae.com/docs'))
        self.assertIsNot(query_host, None)
        self.assertEqual(query_host.url, 'http://infrae.com/docs')

        # Test rewrites
        query_rule, index = query_host.query(('docs', 'index',))
        self.assertIsNot(query_rule, None)
        self.assertEqual(index, 1)
        self.assertEqual(query_rule.url, 'http://infrae.com/docs')
        self.assertEqual(query_rule.path, ('root',))
        self.assertEqual(query_rule.server_url, 'http://infrae.com')
        self.assertEqual(query_rule.server_script, ['docs'])

        query_rule, index = query_host.query(('docs', 'hidden', 'advanced', 'index',))
        self.assertIsNot(query_rule, None)
        self.assertEqual(index, 3)
        self.assertEqual(query_rule.url, 'http://infrae.com/docs/hidden/advanced')
        self.assertEqual(query_rule.path, ('root', 'docs', 'dev'))
        self.assertEqual(query_rule.server_url, 'http://infrae.com')
        self.assertEqual(query_rule.server_script, ['docs', 'hidden', 'advanced'])

        query_rule, index = query_host.query(('docs', 'admin', 'index',))
        self.assertIsNot(query_rule, None)
        self.assertEqual(index, 2)
        self.assertEqual(query_rule.url, 'http://infrae.com/docs/admin')
        self.assertEqual(query_rule.path, ('root', 'docs', 'admin'))
        self.assertEqual(query_rule.server_url, 'http://infrae.com')
        self.assertEqual(query_rule.server_script, ['docs', 'admin'])

        # Test query
        query_host = service.query(url2tuple('http://infrae.com'))
        self.assertIsNot(query_host, None)
        self.assertEqual(query_host.url, 'http://infrae.com')

        # Test rewrite
        query_rule, index = query_host.query(('silva', 'index',))
        self.assertIsNot(query_rule, None)
        self.assertEqual(index, 1)
        self.assertEqual(query_rule.url, 'http://infrae.com/silva')
        self.assertEqual(query_rule.path, ('root',))
        self.assertEqual(query_rule.server_url, 'http://infrae.com')
        self.assertEqual(query_rule.server_script, ['silva'])

    def test_import_csv_invalid(self):
        """Test import the hosts from a CSV that have the wrong number
        of values on one of the lines.
        """
        service = queryUtility(IForestService)
        self.assertEqual(service.get_hosts(), [])

        with self.layer.open_fixture('invalid_hosts.csv') as hosts:
            with self.assertRaises(ValueError):
                service.import_csv(hosts)

        # Nothing changed
        self.assertEqual(service.get_hosts(), [])

    def test_import_csv_duplicate(self):
        """Test import the hosts from a CSV that contains duplicates.
        """
        service = queryUtility(IForestService)
        self.assertEqual(service.get_hosts(), [])

        with self.layer.open_fixture('duplicate_hosts.csv') as hosts:
            with self.assertRaises(ValueError):
                service.import_csv(hosts)

        # Nothing changed
        self.assertEqual(service.get_hosts(), [])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ServiceTestCase))
    suite.addTest(unittest.makeSuite(ServiceImportExportTestCase))
    return suite
