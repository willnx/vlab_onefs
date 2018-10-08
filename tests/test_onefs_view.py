# -*- coding: UTF-8 -*-
"""
A suite of tests for the onefsView object
"""
import unittest
from unittest.mock import patch, MagicMock

import ujson
from flask import Flask
from vlab_api_common import flask_common
from vlab_api_common.http_auth import generate_test_token


from vlab_onefs_api.lib.views import onefs


class TestOneFSView(unittest.TestCase):
    """A set of test cases for the OneFSView object"""
    @classmethod
    def setUpClass(cls):
        """Runs once for the whole test suite"""
        cls.token = generate_test_token(username='bob')

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        app = Flask(__name__)
        onefs.OneFSView.register(app)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        # Mock Celery
        app.celery_app = MagicMock()
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


if __name__ == '__main__':
    unittest.main()
