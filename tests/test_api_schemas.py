# -*- coding: UTF-8 -*-
"""
A suite of tests for the HTTP API schemas
"""
import unittest

from jsonschema import Draft4Validator, validate, ValidationError
from vlab_onefs_api.lib.views import onefs


class TestOneFSViewSchema(unittest.TestCase):
    """A set of test cases for the schemas of /api/1/inf/onefs"""

    def test_post_schema(self):
        """The schema defined for POST is valid"""
        try:
            Draft4Validator.check_schema(onefs.OneFSView.POST_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_delete_schema(self):
        """The schema defined for DELETE is valid"""
        try:
            Draft4Validator.check_schema(onefs.OneFSView.DELETE_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_get_schema(self):
        """The schema defined for GET is valid"""
        try:
            Draft4Validator.check_schema(onefs.OneFSView.GET_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_images_schema(self):
        """The schema defined for GET on /images is valid"""
        try:
            Draft4Validator.check_schema(onefs.OneFSView.IMAGES_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_config_schema(self):
        """The schema defined for POST on /config is valid"""
        try:
            Draft4Validator.check_schema(onefs.OneFSView.CONFIG_SCHEMA)
            schema_valid = True
        except RuntimeError:
            schema_valid = False

        self.assertTrue(schema_valid)

    def test_delete(self):
        """The DELETE schema happy path test"""
        body = {'name': "isi01"}
        try:
            validate(body, onefs.OneFSView.DELETE_SCHEMA)
            ok = True
        except ValidationError:
            ok = False

        self.assertTrue(ok)

    def test_delete_required(self):
        """The DELETE schema requires the parameter 'name'"""
        body = {}
        try:
            validate(body, onefs.OneFSView.DELETE_SCHEMA)
            ok = False
        except ValidationError:
            ok = True

        self.assertTrue(ok)

    def test_post(self):
        """The POST schema happy path test"""
        body = {'name': "isi01",
                'frontend': "externalNetwork",
                'backend': "internalNetwork",
                'image': "8.0.0.4"}
        try:
            validate(body, onefs.OneFSView.POST_SCHEMA)
            ok = True
        except ValidationError:
            ok = False

        self.assertTrue(ok)

    def test_post_name_required(self):
        """The POST schema requires the 'name' parameter"""
        body = { 'frontend': "externalNetwork",
                 'backend': "internalNetwork",
                 'image': "8.0.0.4"}
        try:
            validate(body, onefs.OneFSView.POST_SCHEMA)
            ok = False
        except ValidationError:
            ok = True

        self.assertTrue(ok)

    def test_post_frontend_required(self):
        """The POST schema requires the 'frontend' parameter"""
        body = { 'name': "isi01",
                 'backend': "internalNetwork",
                 'image': "8.0.0.4"}
        try:
            validate(body, onefs.OneFSView.POST_SCHEMA)
            ok = False
        except ValidationError:
            ok = True

        self.assertTrue(ok)

    def test_post_image_required(self):
        """The POST schema requires the 'image' parameter"""
        body = { 'name': "isi01",
                 'frontend': "externalNetwork",
                 'backend': "internalNetwork",}
        try:
            validate(body, onefs.OneFSView.POST_SCHEMA)
            ok = False
        except ValidationError:
            ok = True

        self.assertTrue(ok)

    def test_post_backend_required(self):
        """The POST schema requires the 'image' parameter"""
        body = { 'name': "isi01",
                 'frontend': "externalNetwork",
                 'image': "8.0.0.4"}
        try:
            validate(body, onefs.OneFSView.POST_SCHEMA)
            ok = False
        except ValidationError:
            ok = True

        self.assertTrue(ok)

    def test_config_join(self):
        """The schema for /config supports joining a node to a cluster"""
        body = {'name': 'woot-2',
                'cluster_name': 'woot',
                'join': True}
        try:
            validate(body, onefs.OneFSView.CONFIG_SCHEMA)
            ok = True
        except ValidationError:
            ok = False

        self.assertTrue(ok)

    def test_config_new(self):
        """The schema for /config supports creating a new cluster"""
        body = {'cluster_name': "woot",
                'version': "8.0.1.2",
                'name': 'woot-1',
                'int_netmask': '255.255.255.0',
                'int_ip_low': '200.1.1.1',
                'int_ip_high': '200.1.1.10',
                'ext_netmask': '255.255.255.0',
                'ext_ip_low': '10.7.1.2',
                'ext_ip_high': '10.7.1.10',
                'gateway': '10.7.1.1',
                'encoding': "utf-8",
                'sc_zonename': 'woot.vlab.local',
                'smartconnect_ip': '10.7.1.11',
                'dns_servers': ['1.1.1.1', '8.8.8.8']
               }
        try:
            validate(body, onefs.OneFSView.CONFIG_SCHEMA)
            ok = True
        except ValidationError:
            ok = False

        self.assertTrue(ok)

    def test_config_join_mutext(self):
        """The supplying 'join' when creating a new cluster is invalid on /config """
        body = {'cluster_name': "woot",
                'version': "8.0.1.2",
                'name': 'woot-1',
                'int_netmask': '255.255.255.0',
                'int_ip_low': '200.1.1.1',
                'int_ip_high': '200.1.1.10',
                'ext_netmask': '255.255.255.0',
                'ext_ip_low': '10.7.1.2',
                'ext_ip_high': '10.7.1.10',
                'gateway': '10.7.1.1',
                'encoding': "utf-8",
                'sc_zonename': 'woot.vlab.local',
                'smartconnect_ip': '10.7.1.11',
                'dns_servers': ['1.1.1.1', '8.8.8.8'],
                'join' : True,
               }
        try:
            validate(body, onefs.OneFSView.CONFIG_SCHEMA)
            ok = False
        except ValidationError:
            ok = True

        self.assertTrue(ok)


if __name__ == '__main__':
    unittest.main()
