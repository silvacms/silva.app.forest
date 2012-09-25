# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from ..utils import url2tuple

from zExceptions import BadRequest


class UtilsTestCase(unittest.TestCase):

    def test_url2tuple(self):
        self.assertEqual(
            url2tuple('http://infrae.com'),
            ('http', 'infrae.com', '80'))
        self.assertEqual(
            url2tuple('http://infrae.com/docs/admin'),
            ('http', 'infrae.com', '80', 'docs', 'admin'))
        self.assertEqual(
            url2tuple('http://infrae.com/./docs//admin/..'),
            ('http', 'infrae.com', '80', 'docs'))
        self.assertEqual(
            url2tuple('https://infrae.com/docs/admin'),
            ('https', 'infrae.com', '443', 'docs', 'admin'))
        self.assertEqual(
            url2tuple('http://infrae.com:8081/docs'),
            ('http', 'infrae.com', '8081', 'docs'))
        self.assertEqual(
            url2tuple('https://infrae.com:8081/manage'),
            ('https', 'infrae.com', '8081', 'manage'))

        with self.assertRaises(BadRequest):
            url2tuple('http://infrae.com/../docs/admin')
        with self.assertRaises(BadRequest):
            url2tuple('http://infrae.com/docs/../../..')



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UtilsTestCase))
    return suite


