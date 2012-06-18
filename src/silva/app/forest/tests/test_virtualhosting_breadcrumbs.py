
import unittest

from zope.component import getMultiAdapter, getUtility

from Products.Silva.testing import TestRequest
from infrae.wsgi.interfaces import IVirtualHosting
from silva.core.views.interfaces import IContentURL

from ..interfaces import IForestService
from ..service import VirtualHost, Rewrite
from ..testing import FunctionalLayer


class BreadcrumbTestCase(unittest.TestCase):
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

class DefaultBreadcrumbTestCase(BreadcrumbTestCase):

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
        self.assertEqual(
            url.breadcrumbs(),
            ({'name': u'root',
              'url': 'http://localhost/root'},))

        url = getMultiAdapter((self.root.docs.dev, request), IContentURL)
        self.assertEqual(
            url.breadcrumbs(),
            ({'name': u'root',
              'url': 'http://localhost/root'},
             {'name': u'Documentation',
              'url': 'http://localhost/root/docs'},
             {'name': u'Developer',
              'url': 'http://localhost/root/docs/dev'}))


class ActivatedBreadcrumbTestCase(BreadcrumbTestCase):

    def setUp(self):
        super(ActivatedBreadcrumbTestCase, self).setUp()
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
        self.assertEqual(path, [])

        url = getMultiAdapter((self.root, request), IContentURL)
        self.assertEqual(
            url.breadcrumbs(),
            ({'name': u'root',
              'url': 'http://localhost/root'},))

        url = getMultiAdapter((self.root.docs.dev, request), IContentURL)
        self.assertEqual(
            url.breadcrumbs(),
            ({'name': u'root',
              'url': 'http://localhost/root', },
             {'name': u'Documentation',
              'url': 'http://localhost/root/docs'},
             {'name': u'Developer',
              'url': 'http://localhost/root/docs/dev'}))


class OneRuleBreadcrumbTestCase(BreadcrumbTestCase):

    def setUp(self):
        super(OneRuleBreadcrumbTestCase, self).setUp()
        service = getUtility(IForestService)
        service.set_hosts([
                VirtualHost(
                    'http://localhost/',
                    [],
                    [Rewrite('/', 'root', None)])])
        service.activate()

    def test_activated(self):
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
        self.assertEqual(
            url.breadcrumbs(),
            ({'name': u'root',
              'url': 'http://localhost'},))

        url = getMultiAdapter((self.root.docs.dev, request),IContentURL)
        self.assertEqual(
            url.breadcrumbs(),
            ({'name': u'root',
              'url': 'http://localhost'},
             {'name': u'Documentation',
              'url': 'http://localhost/docs'},
             {'name': u'Developer',
              'url': 'http://localhost/docs/dev'}))


class MultipleRuleBreadcrumbTestCase(BreadcrumbTestCase):

    def setUp(self):
        super(MultipleRuleBreadcrumbTestCase, self).setUp()
        service = getUtility(IForestService)
        service.set_hosts([
                VirtualHost(
                    'http://localhost/',
                    [],
                    [Rewrite('/', '/root', None),
                     Rewrite('/admin', '/root/docs/admin', None),
                     Rewrite('/hidden/docs', '/root/docs/dev', None)])])
        service.activate()

    def test_rewritten_activated(self):
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
        self.assertEqual(
            url.breadcrumbs(),
            ({'name': u'root',
              'url': 'http://localhost'},))

    def test_rewritten_short_activated(self):
        request = TestRequest(
            application=self.root,
            url='http://localhost/admin/manual',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root.docs.admin)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['manual'])

        url = getMultiAdapter((self.root.docs.admin, request), IContentURL)
        self.assertEqual(
            url.breadcrumbs(),
            ({'name': u'Administrator',
              'url': 'http://localhost/admin'},))

    def test_rewritten_short_long(self):
        request = TestRequest(
            application=self.root,
            url='http://localhost/hidden/docs/resources/api',
            headers=[('X-VHM-Url', 'http://localhost')])
        plugin = request.query_plugin(request.application, IVirtualHosting)
        root, method, path = plugin(request.method, request.path)
        self.assertEqual(root, self.root.docs.dev)
        self.assertEqual(method, 'index_html')
        self.assertEqual(path, ['api', 'resources'])

        url = getMultiAdapter(
            (self.root.docs.dev.resources, request),
            IContentURL)
        self.assertEqual(
            url.breadcrumbs(),
            ({'name': u'Developer',
              'url': 'http://localhost/hidden/docs'},
             {'name': u'Resources',
              'url': 'http://localhost/hidden/docs/resources'},))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DefaultBreadcrumbTestCase))
    suite.addTest(unittest.makeSuite(ActivatedBreadcrumbTestCase))
    suite.addTest(unittest.makeSuite(OneRuleBreadcrumbTestCase))
    suite.addTest(unittest.makeSuite(MultipleRuleBreadcrumbTestCase))
    return suite
