# -*- coding: UTF-8 -*-
"""
A suite of tests for the onefsView object
"""
import unittest
from unittest.mock import patch, MagicMock

import ujson
from flask import Flask
from vlab_api_common import flask_common
from vlab_api_common.http_auth import generate_v2_test_token


from vlab_onefs_api.lib.views import onefs


class TestOneFSView(unittest.TestCase):
    """A set of test cases for the OneFSView object"""
    @classmethod
    def setUpClass(cls):
        """Runs once for the whole test suite"""
        cls.token = generate_v2_test_token(username='bob')

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        app = Flask(__name__)
        onefs.OneFSView.register(app)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        # Mock Celery
        cls.celery_app = MagicMock()
        app.celery_app = cls.celery_app
        cls.fake_task = MagicMock()
        cls.fake_task.id = 'asdf-asdf-asdf'
        app.celery_app.send_task.return_value = cls.fake_task

    def test_get_task(self):
        """OneFSView - GET on /api/1/inf/onefs returns a task-id"""
        resp = self.app.get('/api/1/inf/onefs',
                            headers={'X-Auth': self.token})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_get_task_link(self):
        """OneFSView - GET on /api/1/inf/onefs sets the Link header"""
        resp = self.app.get('/api/1/inf/onefs',
                            headers={'X-Auth': self.token})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/1/inf/onefs/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_post_task(self):
        """OneFSView - POST on /api/1/inf/onefs returns a task-id"""
        resp = self.app.post('/api/1/inf/onefs',
                             headers={'X-Auth': self.token},
                             json={'name': "isiO1",
                                   'image': "8.0.0.4",
                                   'frontend': "externalNetwork",
                                   'backend': "internalNetwork"})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_post_task_link(self):
        """OneFSView - POST on /api/1/inf/onefs sets the Link header"""
        resp = self.app.post('/api/1/inf/onefs',
                             headers={'X-Auth': self.token},
                             json={'name': "isiO1",
                                   'image': "8.0.0.4",
                                   'frontend': "externalNetwork",
                                   'backend': "internalNetwork"})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/1/inf/onefs/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_delete_task(self):
        """OneFSView - DELETE on /api/1/inf/onefs returns a task-id"""
        resp = self.app.delete('/api/1/inf/onefs',
                               headers={'X-Auth': self.token},
                               json={'name': "isi01"})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_delete_task_link(self):
        """OneFSView - DELETE on /api/1/inf/onefs sets the Link header"""
        resp = self.app.delete('/api/1/inf/onefs',
                               headers={'X-Auth': self.token},
                               json={'name': "isi01"})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/1/inf/onefs/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_get_image_task(self):
        """OneFSView - GET on /api/1/inf/onefs/image returns a task-id"""
        resp = self.app.get('/api/1/inf/onefs/image',
                            headers={'X-Auth': self.token})

        task_id = resp.json['content']['task-id']
        expected = 'asdf-asdf-asdf'

        self.assertEqual(task_id, expected)

    def test_get_image_task_link(self):
        """OneFSView - GET on /api/1/inf/onefs/image sets the Link header"""
        resp = self.app.get('/api/1/inf/onefs/image',
                            headers={'X-Auth': self.token})

        task_id = resp.headers['Link']
        expected = '<https://localhost/api/1/inf/onefs/task/asdf-asdf-asdf>; rel=status'

        self.assertEqual(task_id, expected)

    def test_post_config_ok(self):
        """OneFSView - POST on /api/1/inf/onefs/config returns 202 upon success"""
        payload = {"cluster_name": "mycluster",
                   "name": "mycluster-1",
                   "version": "8.0.0.4",
                   "int_netmask": "255.255.255.0",
                   "int_ip_low": "4.4.4.4",
                   "int_ip_high": "4.4.4.40",
                   "ext_netmask": "255.255.255.0",
                   "ext_ip_low": "10.1.1.2",
                   "ext_ip_high": "10.1.1.20",
                   "smartconnect_ip": "10.1.1.21",
                   "gateway": "10.1.1.1",
                   "encoding": "utf-8",
                   "sc_zonename": "myzone.foo.com",
                   "dns_servers": ['1.1.1.1', '8.8.8.8']
                  }
        resp = self.app.post('/api/1/inf/onefs/config',
                             json=payload,
                             headers={'X-Auth': self.token})
        expected = 202

        self.assertEqual(resp.status_code, expected)

    def test_post_config_bad_input(self):
        """OneFSView - POST on /api/1/inf/onefs/config returns 400 when supplied with bad input"""
        payload = {"cluster_name": "mycluster",
                   "name": "mycluster-1",
                   "version": "8.0.0.4",
                   "int_netmask": "255.255.255.0",
                   "int_ip_low": "4.4.4.4",
                   "int_ip_high": "4.4.4.40",
                   "ext_netmask": "255.255.255.0",
                   "ext_ip_low": "10.100.1.2",
                   "ext_ip_high": "10.1.1.20",
                   "smartconnect_ip": "10.1.1.21",
                   "gateway": "10.1.1.1",
                   "encoding": "utf-8",
                   "sc_zonename": "myzone.foobar.com",
                   "dns_servers": ['1.1.1.1', '8.8.8.8']
                  }
        resp = self.app.post('/api/1/inf/onefs/config',
                             json=payload,
                             headers={'X-Auth': self.token})
        expected = 400

        self.assertEqual(resp.status_code, expected)

    def test_post_config_compliance_default(self):
        """OneFSView - POST on /api/1/inf/onefs/config - the 'compliance' param defaults to False"""
        payload = {"cluster_name": "mycluster",
                   "name": "mycluster-1",
                   "version": "8.0.0.4",
                   "int_netmask": "255.255.255.0",
                   "int_ip_low": "4.4.4.4",
                   "int_ip_high": "4.4.4.40",
                   "ext_netmask": "255.255.255.0",
                   "ext_ip_low": "10.1.1.2",
                   "ext_ip_high": "10.1.1.20",
                   "smartconnect_ip": "10.1.1.21",
                   "gateway": "10.1.1.1",
                   "encoding": "utf-8",
                   "sc_zonename": "myzone.foo.com",
                   "dns_servers": ['1.1.1.1', '8.8.8.8']
                  }
        resp = self.app.post('/api/1/inf/onefs/config',
                             json=payload,
                             headers={'X-Auth': self.token})

        _, the_kwargs = self.celery_app.send_task.call_args
        compliance = the_kwargs['kwargs']['compliance']

        self.assertFalse(compliance)

    def test_post_config_compliance(self):
        """OneFSView - POST on /api/1/inf/onefs/config - the 'compliance' is a boolean when set"""
        payload = {"cluster_name": "mycluster",
                   "name": "mycluster-1",
                   "version": "8.0.0.4",
                   "int_netmask": "255.255.255.0",
                   "int_ip_low": "4.4.4.4",
                   "int_ip_high": "4.4.4.40",
                   "ext_netmask": "255.255.255.0",
                   "ext_ip_low": "10.1.1.2",
                   "ext_ip_high": "10.1.1.20",
                   "smartconnect_ip": "10.1.1.21",
                   "gateway": "10.1.1.1",
                   "encoding": "utf-8",
                   "sc_zonename": "myzone.foo.com",
                   "compliance" : True,
                   "dns_servers": ['1.1.1.1', '8.8.8.8']
                  }
        resp = self.app.post('/api/1/inf/onefs/config',
                             json=payload,
                             headers={'X-Auth': self.token})

        _, the_kwargs = self.celery_app.send_task.call_args
        compliance = the_kwargs['kwargs']['compliance']

        self.assertTrue(compliance is True) # test for type, there is only one "True" object ever


if __name__ == '__main__':
    unittest.main()
