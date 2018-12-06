# -*- coding: UTF-8 -*-
"""
A suite of tests for the functions in tasks.py
"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_onefs_api.lib.worker import tasks


class TestTasks(unittest.TestCase):
    """A set of test cases for tasks.py"""
    @patch.object(tasks, 'vmware')
    def test_show_ok(self, fake_vmware):
        """``show`` returns a dictionary when everything works as expected"""
        fake_vmware.show_onefs.return_value = {'worked': True}

        output = tasks.show(username='bob', txn_id='myId')
        expected = {'content' : {'worked': True}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    def test_show_value_error(self, fake_vmware):
        """``show`` sets the error in the dictionary to the ValueError message"""
        fake_vmware.show_onefs.side_effect = [ValueError("testing")]

        output = tasks.show(username='bob', txn_id='myId')
        expected = {'content' : {}, 'error': 'testing', 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    def test_create_ok(self, fake_vmware):
        """``create`` returns a dictionary when everything works as expected"""
        fake_vmware.create_onefs.return_value = {'worked': True}

        output = tasks.create(username='bob',
                              machine_name='isi01',
                              image='8.0.04',
                              front_end='externalNetwork',
                              back_end='internalNetwork',
                              txn_id='myId')
        expected = {'content' : {'worked': True}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    def test_create_value_error(self, fake_vmware):
        """``create`` sets the error in the dictionary to the ValueError message"""
        fake_vmware.create_onefs.side_effect = [ValueError("testing")]

        output = tasks.create(username='bob',
                              machine_name='isi01',
                              image='8.0.04',
                              front_end='externalNetwork',
                              back_end='internalNetwork',
                              txn_id='myId')
        expected = {'content' : {}, 'error': 'testing', 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    def test_delete_ok(self, fake_vmware):
        """``delete`` returns a dictionary when everything works as expected"""
        fake_vmware.delete_onefs.return_value = {'worked': True}

        output = tasks.delete(username='bob', machine_name='isi01', txn_id='myId')
        expected = {'content' : {}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    def test_delete_value_error(self, fake_vmware):
        """``delete`` sets the error in the dictionary to the ValueError message"""
        fake_vmware.delete_onefs.side_effect = [ValueError("testing")]

        output = tasks.delete(username='bob', machine_name='isi01', txn_id='myId')
        expected = {'content' : {}, 'error': 'testing', 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    def test_image(self, fake_vmware):
        """``image`` returns a dictionary when everything works as expected"""
        fake_vmware.list_images.return_value = []

        output = tasks.image(txn_id='myId')
        expected = {'content' : {'image': []}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    @patch.object(tasks, 'setup_onefs')
    def test_config(self, fake_setup_onefs, fake_vmware):
        """``config`` returns a dictionary upon success"""
        fake_vmware.show_onefs.return_value = {'mycluster-1' : {'console': 'https://htmlconsole.com',
                                                                'info': {'configured': False}}}

        output = tasks.config(cluster_name='mycluster',
                              name='mycluster-1',
                              username='bob',
                              version='8.1.1.0',
                              int_netmask='255.255.255.0',
                              int_ip_low='5.5.5.1',
                              int_ip_high='5.5.5.10',
                              ext_netmask='255.255.255.0',
                              ext_ip_low='10.1.1.2',
                              ext_ip_high='10.1.1.20',
                              gateway='10.1.1.1',
                              dns_servers='1.1.1.1,8.8.8.8',
                              encoding='utf-8',
                              sc_zonename='myzone.foo.com',
                              smartconnect_ip='10.1.1.21',
                              join_cluster=False,
                              txn_id='myId')
        expected = {'content': {}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    @patch.object(tasks, 'setup_onefs')
    def test_config_join(self, fake_setup_onefs, fake_vmware):
        """``config`` returns a dictionary upon joining a node to an existing cluster"""
        fake_vmware.show_onefs.return_value = {'mycluster-1' : {'console': 'https://htmlconsole.com',
                                                                'info': {'configured': False}}}

        output = tasks.config(cluster_name='mycluster',
                              name='mycluster-1',
                              username='bob',
                              version='8.1.1.0',
                              int_netmask='255.255.255.0',
                              int_ip_low='5.5.5.1',
                              int_ip_high='5.5.5.10',
                              ext_netmask='255.255.255.0',
                              ext_ip_low='10.1.1.2',
                              ext_ip_high='10.1.1.20',
                              gateway='10.1.1.1',
                              dns_servers='1.1.1.1,8.8.8.8',
                              encoding='utf-8',
                              sc_zonename='myzone.foo.com',
                              smartconnect_ip='10.1.1.21',
                              join_cluster=True,
                              txn_id='myId')
        expected = {'content': {}, 'error': None, 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    @patch.object(tasks, 'setup_onefs')
    def test_config_no_node(self, fake_setup_onefs, fake_vmware):
        """``config`` returns an error if unable to find the node to configure"""
        fake_vmware.show_onefs.return_value = {}

        output = tasks.config(cluster_name='mycluster',
                              name='mycluster-1',
                              username='bob',
                              version='8.1.1.0',
                              int_netmask='255.255.255.0',
                              int_ip_low='5.5.5.1',
                              int_ip_high='5.5.5.10',
                              ext_netmask='255.255.255.0',
                              ext_ip_low='10.1.1.2',
                              ext_ip_high='10.1.1.20',
                              gateway='10.1.1.1',
                              dns_servers='1.1.1.1,8.8.8.8',
                              encoding='utf-8',
                              sc_zonename='myzone.foo.com',
                              smartconnect_ip='10.1.1.21',
                              join_cluster=False,
                              txn_id='myId')
        expected = {'content': {}, 'error': 'No node named mycluster-1 found', 'params': {}}

        self.assertEqual(output, expected)

    @patch.object(tasks, 'vmware')
    @patch.object(tasks, 'setup_onefs')
    def test_config_already_configed(self, fake_setup_onefs, fake_vmware):
        """``config`` returns an error if the node is already configured"""
        fake_vmware.show_onefs.return_value = {'mycluster-1' : {'console': 'https://htmlconsole.com',
                                                                'info': {'configured': True}}}


        output = tasks.config(cluster_name='mycluster',
                              name='mycluster-1',
                              username='bob',
                              version='8.1.1.0',
                              int_netmask='255.255.255.0',
                              int_ip_low='5.5.5.1',
                              int_ip_high='5.5.5.10',
                              ext_netmask='255.255.255.0',
                              ext_ip_low='10.1.1.2',
                              ext_ip_high='10.1.1.20',
                              gateway='10.1.1.1',
                              dns_servers='1.1.1.1,8.8.8.8',
                              encoding='utf-8',
                              sc_zonename='myzone.foo.com',
                              smartconnect_ip='10.1.1.21',
                              join_cluster=False,
                              txn_id='myId')
        expected = {'content': {}, 'error': "Cannot configure a node that's already configured", 'params': {}}

        self.assertEqual(output, expected)


if __name__ == '__main__':
    unittest.main()
