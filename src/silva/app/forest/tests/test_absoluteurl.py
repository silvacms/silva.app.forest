# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from zope.interface.verify import verifyObject
from zope import component

from silva.core.views.interfaces import IContentURL
from Products.Silva.testing import TestRequest

from ..interfaces import IForestService
from ..service import VirtualHost, Rewrite
from ..testing import FunctionalLayer


class ForestURLTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()

    def test_not_activated(self):
        request = TestRequest(application=self.root)
        url = component.getMultiAdapter((self.root, request), IContentURL)
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

    def test_activated_default(self):
        service = component.getUtility(IForestService)
        service.activate()

        request = TestRequest(application=self.root)
        url = component.getMultiAdapter((self.root, request), IContentURL)
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

    def test_activated_one_rule(self):
        service = component.getUtility(IForestService)
        service.set_hosts([
                VirtualHost(
                    'http://localhost/',
                    [],
                    [Rewrite('/', '/root', None)])
                ])
        service.activate()

        request = TestRequest(application=self.root)
        url = component.getMultiAdapter((self.root, request), IContentURL)
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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ForestURLTestCase))
    return suite
