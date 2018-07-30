# -*- coding: UTF-8 -*-
"""
A suite of unit tests for the VlanView object
"""
import unittest
from unittest.mock import patch, MagicMock

import ujson
from flask import Flask
from vlab_api_common import flask_common

from vlab_onefs_api.lib.views import healthcheck


class TestHealthView(unittest.TestCase):
    """A suite of test cases for the HealthView object"""

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        app = Flask(__name__)
        healthcheck.HealthView.register(app)
        app.config['TESTING'] = True
        cls.app = app.test_client()

    def test_get(self):
        """HealthView for /api/1/inf/vlan/heathcheck supports GET"""
        resp = self.app.get('/api/1/inf/onefs/healthcheck')

        expected = 200

        self.assertEqual(resp.status_code, expected)


if __name__ == '__main__':
    unittest.main()
