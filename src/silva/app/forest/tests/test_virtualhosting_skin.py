# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt


import unittest

from zope.component import getUtility

from silvatheme.standardissue.standardissue import IStandardIssueSkin
from silvatheme.multiflex.multiflex import IMultiflexSkin
from silva.core.layout.traverser import SET_SKIN_ALLOWED_FLAG
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
        service = getUtility(IForestService)
        service.set_hosts([
                VirtualHost(
                    'http://localhost/',
                    [],
                    [Rewrite('/', '/root', 'Multiflex'),
                     Rewrite('/docs', '/root/docs', None),
                     Rewrite('/user', '/root/docs/user', 'Multiflex', False)])
                ])
        service.activate()

    def test_skin_not_activated(self):
        request = TestRequest(
            application=self.root,
            url='http://localhost')
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, request.application)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, [])
        self.assertFalse(IMultiflexSkin.providedBy(request))

    def test_skin_root(self):
        request = TestRequest(
            application=self.root,
            url='http://localhost',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, [])
        self.assertTrue(IMultiflexSkin.providedBy(request))
        self.assertFalse(IStandardIssueSkin.providedBy(request))
        self.assertFalse(request.get(SET_SKIN_ALLOWED_FLAG, True))

    def test_skin_folder_fallback_default(self):
        request = TestRequest(
            application=self.root,
            url='http://localhost/docs/admin',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root.docs)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['admin'])
        self.assertFalse(IMultiflexSkin.providedBy(request))
        self.assertTrue(IStandardIssueSkin.providedBy(request))
        self.assertTrue(request.get(SET_SKIN_ALLOWED_FLAG, True))

    def test_skin_folder_not_enforced(self):
        request = TestRequest(
            application=self.root,
            url='http://localhost/user/information',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root.docs.user)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['information'])
        self.assertTrue(IMultiflexSkin.providedBy(request))
        self.assertFalse(IStandardIssueSkin.providedBy(request))
        self.assertTrue(request.get(SET_SKIN_ALLOWED_FLAG, True))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(VirtualHostingTestCase))
    return suite
