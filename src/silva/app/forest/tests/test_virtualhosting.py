# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from zope.interface.verify import verifyObject
from zope.component import getUtility, getMultiAdapter

from silva.core.views.interfaces import IContentURL
from Products.Silva.testing import TestRequest

from infrae.wsgi.interfaces import IVirtualHosting

from ..interfaces import IForestService
from ..service import VirtualHost, Rewrite
from ..testing import FunctionalLayer


class VirtualHostingTestCase(unittest.TestCase):
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
        factory.manage_addFolder('resources', 'Resources')


class DefaultHostingTestCase(VirtualHostingTestCase):

    def test_not_activated(self):
        request = TestRequest(
            application=self.root,
            url='http://localhost')
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, request.application)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, [])

        url = getMultiAdapter((self.root, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/root')
        self.assertEqual(
            url.url(),
            'http://localhost/root')
        self.assertEqual(
            url.url(relative=True),
            '/root')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/root/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/root/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/root/++preview++')


class ActivatedVirtualHostingTestCase(VirtualHostingTestCase):

    def setUp(self):
        super(ActivatedVirtualHostingTestCase, self).setUp()
        service = getUtility(IForestService)
        service.activate()

    def test_activated_default(self):
        request = TestRequest(
            application=self.root,
            url='http://localhost')
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, request.application)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, request.path)

        url = getMultiAdapter((self.root, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/root')
        self.assertEqual(
            url.url(),
            'http://localhost/root')
        self.assertEqual(
            url.url(relative=True),
            '/root')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/root/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/root/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/root/++preview++')


class OneRuleHostingTestCase(VirtualHostingTestCase):

    def setUp(self):
        super(OneRuleHostingTestCase, self).setUp()
        # Add a simple rule.
        service = getUtility(IForestService)
        service.set_hosts([
                VirtualHost(
                    'http://localhost/',
                    [],
                    [Rewrite('/', '/root', None)])
                ])
        service.activate()

    def test_root_different_host(self):
        """Rewriting is applied even if the URL have not the same
        domain, but the header is present.
        """
        request = TestRequest(
            application=self.root,
            url='http://development.server.corp/docs',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['docs'])
        self.assertEqual('http://localhost/docs', request['ACTUAL_URL'])

        url = getMultiAdapter((self.root, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost')
        self.assertEqual(
            url.url(),
            'http://localhost')
        self.assertEqual(
            url.url(relative=True),
            '/')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/++preview++')

    def test_root_not_applied(self):
        """Rewriting is not applied if the header is not present.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/docs')
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, request.application)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['docs'])
        self.assertEqual('http://localhost/docs', request['ACTUAL_URL'])

        url = getMultiAdapter((self.root, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/root')
        self.assertEqual(
            url.url(),
            'http://localhost/root')
        self.assertEqual(
            url.url(relative=True),
            '/root')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/root/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/root/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/root/++preview++')

    def test_root(self):
        """If the header is present, rewriting is applied.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, [])

        url = getMultiAdapter((self.root, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost')
        self.assertEqual(
            url.url(),
            'http://localhost')
        self.assertEqual(
            url.url(relative=True),
            '/')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/++preview++')

    def test_folder(self):
        """If the header is present, rewriting is applied. You can
        compute URL of a content inside the same virtual host.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/docs',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['docs'])

        url = getMultiAdapter(
            (self.root.docs.user, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/docs/user')
        self.assertEqual(
            url.url(),
            'http://localhost/docs/user')
        self.assertEqual(
            url.url(relative=True),
            '/docs/user')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/++preview++/docs/user')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/++preview++/docs/user')
        self.assertEqual(
            url.preview(),
            'http://localhost/++preview++/docs/user')

    def test_folder_brain(self):
        """If the header is present, rewriting is applied. You can
        compute the URL of a brain inside the same virtual host.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/docs',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['docs'])

        catalog = root.service_catalog
        brains = catalog(meta_type='Silva Folder', path='/root/docs/user')
        self.assertEqual(len(brains), 1)
        brain = brains[0]

        url = getMultiAdapter((brain, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            brain.getURL(),
            'http://localhost/docs/user')
        self.assertEqual(
            str(url),
            'http://localhost/docs/user')
        self.assertEqual(
            url.url(),
            'http://localhost/docs/user')
        self.assertEqual(
            url.url(relative=True),
            '/docs/user')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/docs/user')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/docs/user')
        self.assertEqual(
            url.preview(),
            'http://localhost/docs/user')

    def test_root_brain(self):
        """If the header is present, rewriting is applied. You can
        compute the URL of a brain inside the same virtual host.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/docs/user',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['user', 'docs'])

        catalog = root.service_catalog
        brains = catalog(meta_type='Silva Root', path='/root')
        self.assertEqual(len(brains), 1)
        brain = brains[0]

        url = getMultiAdapter((brain, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            brain.getURL(),
            'http://localhost')
        self.assertEqual(
            str(url),
            'http://localhost')
        self.assertEqual(
            url.url(),
            'http://localhost')
        self.assertEqual(
            url.url(relative=True),
            '/')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost')
        self.assertEqual(
            url.preview(),
            'http://localhost')


class MultipleRulesHostingTestCase(VirtualHostingTestCase):

    def setUp(self):
        super(MultipleRulesHostingTestCase, self).setUp()
        # Add a simple rule.
        service = getUtility(IForestService)
        service.set_hosts([
                VirtualHost(
                    'http://localhost/',
                    [],
                    [Rewrite('/', '/root', None),
                     Rewrite('/admin', '/root/docs/admin', None),
                     Rewrite('/hidden/docs', '/root/docs/dev', None)])
                ])
        service.activate()

    def test_root(self):
        """If the header is present, rewriting is applied.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/docs',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['docs'])

        url = getMultiAdapter((self.root, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost')
        self.assertEqual(
            url.url(),
            'http://localhost')
        self.assertEqual(
            url.url(relative=True),
            '/')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/++preview++')

    def test_folder_rewritten_short(self):
        """If the header is present, rewriting is applied.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/admin',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root.docs.admin)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, [])

        url = getMultiAdapter((self.root.docs.admin, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/admin')
        self.assertEqual(
            url.url(),
            'http://localhost/admin')
        self.assertEqual(
            url.url(relative=True),
            '/admin')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/admin/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/admin/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/admin/++preview++')

        # Get the URL of a different folder
        url = getMultiAdapter((self.root.docs.dev, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/hidden/docs')
        self.assertEqual(
            url.url(),
            'http://localhost/hidden/docs')
        self.assertEqual(
            url.url(relative=True),
            '/hidden/docs')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/hidden/docs/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/hidden/docs/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/hidden/docs/++preview++')

        # Get the URL of a different publication
        url = getMultiAdapter((self.root.docs, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/docs')
        self.assertEqual(
            url.url(),
            'http://localhost/docs')
        self.assertEqual(
            url.url(relative=True),
            '/docs')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/++preview++/docs')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/++preview++/docs')
        self.assertEqual(
            url.preview(),
            'http://localhost/++preview++/docs')

    def test_folder_rewritten_long(self):
        """If the header is present, rewriting is applied.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/hidden/docs/resources',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root.docs.dev)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['resources'])

        url = getMultiAdapter((self.root.docs.admin, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/admin')
        self.assertEqual(
            url.url(),
            'http://localhost/admin')
        self.assertEqual(
            url.url(relative=True),
            '/admin')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/admin/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/admin/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/admin/++preview++')

        # Get the URL of a different folder
        url = getMultiAdapter((root.resources, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/hidden/docs/resources')
        self.assertEqual(
            url.url(),
            'http://localhost/hidden/docs/resources')
        self.assertEqual(
            url.url(relative=True),
            '/hidden/docs/resources')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/hidden/docs/++preview++/resources')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/hidden/docs/++preview++/resources')
        self.assertEqual(
            url.preview(),
            'http://localhost/hidden/docs/++preview++/resources')

        # Get the URL of a different publication
        url = getMultiAdapter((self.root.docs, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/docs')
        self.assertEqual(
            url.url(),
            'http://localhost/docs')
        self.assertEqual(
            url.url(relative=True),
            '/docs')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/++preview++/docs')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/++preview++/docs')
        self.assertEqual(
            url.preview(),
            'http://localhost/++preview++/docs')

    def test_folder_brain_rewritten_long(self):
        """If the header is present, rewriting is applied.
        """
        request = TestRequest(
            application=self.root,
            url='http://localhost/hidden/docs/resources',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root.docs.dev)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['resources'])

        catalog = root.service_catalog
        brains = catalog(meta_type='Silva Folder', path='/root/docs/admin')
        self.assertEqual(len(brains), 1)
        brain = brains[0]

        url = getMultiAdapter((brain, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            brain.getURL(),
            'http://localhost/admin')
        self.assertEqual(
            str(url),
            'http://localhost/admin')
        self.assertEqual(
            url.url(),
            'http://localhost/admin')
        self.assertEqual(
            url.url(relative=True),
            '/admin')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/admin')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/admin')
        self.assertEqual(
            url.preview(),
            'http://localhost/admin')

        # Get the URL of a different brain
        catalog = root.service_catalog
        brains = catalog(
            meta_type='Silva Folder',
            path='/root/docs/dev/resources')
        self.assertEqual(len(brains), 1)
        brain = brains[0]

        url = getMultiAdapter((brain, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            brain.getURL(),
            'http://localhost/hidden/docs/resources')
        self.assertEqual(
            str(url),
            'http://localhost/hidden/docs/resources')
        self.assertEqual(
            url.url(),
            'http://localhost/hidden/docs/resources')
        self.assertEqual(
            url.url(relative=True),
            '/hidden/docs/resources')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/hidden/docs/resources')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/hidden/docs/resources')
        self.assertEqual(
            url.preview(),
            'http://localhost/hidden/docs/resources')

        # Get the URL of a different brain
        catalog = root.service_catalog
        brains = catalog(
            meta_type='Silva Publication',
            path='/root/docs')
        self.assertEqual(len(brains), 1)
        brain = brains[0]

        url = getMultiAdapter((brain, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            brain.getURL(),
            'http://localhost/docs')
        self.assertEqual(
            str(url),
            'http://localhost/docs')
        self.assertEqual(
            url.url(),
            'http://localhost/docs')
        self.assertEqual(
            url.url(relative=True),
            '/docs')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/docs')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/docs')
        self.assertEqual(
            url.preview(),
            'http://localhost/docs')


class MultipleHostsHostingTestCase(VirtualHostingTestCase):

    def setUp(self):
        super(MultipleHostsHostingTestCase, self).setUp()
        # Add a simple rule.
        service = getUtility(IForestService)
        service.set_hosts([
                VirtualHost(
                    'http://localhost/',
                    ['http://frontend.localhost/'],
                    [Rewrite('/', '/root/docs/admin', None),
                     Rewrite('/manual', '/root/docs', None),
                     Rewrite('/info', '/root', None)]),
                VirtualHost(
                    'http://admin.localhost/',
                    ['http://backend.localhost/'],
                    [Rewrite('/', '/root', None)])
                ])
        service.activate()

    def test_frontend(self):
        request = TestRequest(
            application=self.root,
            url='http://localhost',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root.docs.admin)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, [])

        url = getMultiAdapter((self.root.docs.admin, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost')
        self.assertEqual(
            url.url(),
            'http://localhost')
        self.assertEqual(
            url.url(relative=True),
            '/')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/++preview++')

        url = getMultiAdapter((self.root.docs, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/manual')
        self.assertEqual(
            url.url(),
            'http://localhost/manual')
        self.assertEqual(
            url.url(relative=True),
            '/manual')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/manual/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/manual/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/manual/++preview++')

        url = getMultiAdapter((self.root, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            str(url),
            'http://localhost/info')
        self.assertEqual(
            url.url(),
            'http://localhost/info')
        self.assertEqual(
            url.url(relative=True),
            '/info')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/info/++preview++')
        self.assertEqual(
            url.url(preview=True),
            'http://localhost/info/++preview++')
        self.assertEqual(
            url.preview(),
            'http://localhost/info/++preview++')

    def test_frontend_alias(self):
        request = TestRequest(
            application=self.root,
            url='http://frontend.localhost/info',
            headers=[('X-VHM-Url', 'http://frontend.localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, [])

        catalog = root.service_catalog
        brains = catalog(meta_type='Silva Folder', path='/root/docs/admin')
        self.assertEqual(len(brains), 1)
        brain = brains[0]

        url = getMultiAdapter((brain, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            brain.getURL(),
            'http://frontend.localhost')
        self.assertEqual(
            str(url),
            'http://frontend.localhost')
        self.assertEqual(
            url.url(),
            'http://frontend.localhost')
        self.assertEqual(
            url.url(relative=True),
            '/')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/')
        self.assertEqual(
            url.url(preview=True),
            'http://frontend.localhost')
        self.assertEqual(
            url.preview(),
            'http://frontend.localhost')

        catalog = root.service_catalog
        brains = catalog(meta_type='Silva Root', path='/root')
        self.assertEqual(len(brains), 1)
        brain = brains[0]

        url = getMultiAdapter((brain, request), IContentURL)
        self.assertTrue(verifyObject(IContentURL, url))

        self.assertEqual(
            brain.getURL(),
            'http://frontend.localhost/info')
        self.assertEqual(
            str(url),
            'http://frontend.localhost/info')
        self.assertEqual(
            url.url(),
            'http://frontend.localhost/info')
        self.assertEqual(
            url.url(relative=True),
            '/info')
        self.assertEqual(
            url.url(relative=True, preview=True),
            '/info')
        self.assertEqual(
            url.url(preview=True),
            'http://frontend.localhost/info')
        self.assertEqual(
            url.preview(),
            'http://frontend.localhost/info')

    def test_backend(self):
        request = TestRequest(
            application=self.root,
            url='http://admin.localhost/docs/admin',
            headers=[('X-VHM-Url', 'http://admin.localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['admin', 'docs'])

    def test_backend_alias(self):
        request = TestRequest(
            application=self.root,
            url='http://admin.localhost/docs/admin',
            headers=[('X-VHM-Url', 'http://backend.localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['admin', 'docs'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DefaultHostingTestCase))
    suite.addTest(unittest.makeSuite(ActivatedVirtualHostingTestCase))
    suite.addTest(unittest.makeSuite(OneRuleHostingTestCase))
    suite.addTest(unittest.makeSuite(MultipleRulesHostingTestCase))
    suite.addTest(unittest.makeSuite(MultipleHostsHostingTestCase))
    return suite
