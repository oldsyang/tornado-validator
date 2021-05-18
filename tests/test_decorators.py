import json
import os
import random
import sys
from unittest.mock import MagicMock

import tornado.web
import tornado.web
from tornado.testing import AsyncTestCase

sys.path.insert(0, os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from tornado_validator.exceptions import ValidationError

from tornado_validator.decorators import POST, param, POST_OR_GET, HEADER


def get_handler(**kwargs):
    handler = tornado.web.RequestHandler(MagicMock(), MagicMock())
    handler.get_query_argument = lambda k, default=None: kwargs.get(k, default)
    handler.request = MagicMock()
    handler.request.headers = kwargs

    return handler


def post_handler(**kwargs):
    handler = tornado.web.RequestHandler(MagicMock(), MagicMock())
    handler.request = MagicMock()
    handler.request.body_arguments = {k: [bytes(str(val), encoding="utf8")] for k, val in kwargs.items()}
    handler.request.body = bytes(json.dumps(kwargs), encoding="utf8")

    return handler


def post_or_get_handler(**kwargs):
    handler = tornado.web.RequestHandler(MagicMock(), MagicMock())

    flag = random.randint(0, 1)
    if flag:
        _kwargs = {}
        handler.get_query_argument = lambda k, default=None: _kwargs.get(k, default)
        handler.request = MagicMock()
        handler.request.body_arguments = {k: [bytes(str(val), encoding="utf8")] for k, val in kwargs.items()}
        handler.request.body = bytes(json.dumps(kwargs), encoding="utf8")
    else:
        handler.get_query_argument = lambda k, default=None: kwargs.get(k, default)
        handler.request = MagicMock()
        _kwargs = {}
        handler.request.body_arguments = {k: [bytes(str(val), encoding="utf8")] for k, val in _kwargs.items()}
        handler.request.body = bytes(json.dumps(_kwargs), encoding="utf8")

    return handler


class TestSomeHandler(AsyncTestCase):

    def test_get_param_success(self):
        @param('a')
        def view(request, a):
            self.assertEqual(a, 'a')

        view(get_handler(a="a"))

    def test_post_param_success(self):
        @POST('a', type='int', default=0)
        def view(request, a):
            self.assertEqual(a, 1)

        view(post_handler(a=1))

    def test_multiple_in(self):
        @param('a', validators='in: a, b')
        def view(request, a):
            self.assertIn(a, ('a'))

        view(get_handler(a="a"))

    def test_default(self):
        """
        Test decorator with default param.
        """

        # Test param with default value
        @param('a', default='default')
        def view_with_default(request, a):
            self.assertEqual(a, 'default')

        view_with_default(get_handler())

        # Test param without default value
        @param('a')
        def view_without_default(request, a):
            self.assertIsNone(a)

        view_without_default(get_handler())

    def test_many(self):
        @param('a', type='int', default=[1], many=True, separator='|')
        def view(request, a):
            return a

        self.assertEqual(view(get_handler()), [1])
        self.assertEqual(view(get_handler(a="1|2")), [1, 2])

        with self.assertRaises(ValidationError):
            view(get_handler(a='1|a'))

    def test_many_without_default_value(self):
        @param('a', many=True)
        def view(request, a):
            return a

        self.assertEqual(view(get_handler()), [])
        self.assertEqual(view(get_handler(a='1')), ['1'])

    def test_related_name(self):
        @param('a', related_name='b', type='int', default=[1], many=True, separator='|', validators='required')
        def view(request, b):
            return b

        self.assertEqual(view(get_handler()), [1])
        self.assertEqual(view(get_handler(a='1|2')), [1, 2])
        with self.assertRaises(ValidationError):
            view(get_handler(a='1|a'))

    def test_verbose_name(self):
        @param('a', verbose_name='b', type='int', default=[1], many=True, separator='|')
        def view(request, a):
            return a

        self.assertEqual(view(get_handler()), [1])
        self.assertEqual(view(get_handler(a='1|2')), [1, 2])
        with self.assertRaisesRegex(ValidationError, 'b'):
            view(get_handler(a='1|a'))

    def test_header(self):
        @HEADER('a', type='int', default=0)
        def view(request, a):
            return a

        self.assertEqual(view(get_handler(a='1')), 1)  # Pass header via **extra
        self.assertEqual(view(get_handler()), 0)

    def test_post_or_get(self):
        @POST_OR_GET('a', type='int', default=0)
        def view(request, a):
            return a

        self.assertEqual(view(post_or_get_handler(a=1)), 1)
        self.assertEqual(view(post_or_get_handler(a=1)), 1)
        self.assertEqual(view(post_or_get_handler()), 0)
