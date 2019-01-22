# -*- coding: UTF-8 -*-
"""
A suite of tests for the validators.py module
"""
import unittest

from vlab_onefs_api.lib import validators


class TestValidaters(unittest.TestCase):
    """A suite of test cases for the different input validators for /config"""
    def test_to_network(self):
        """``to_network`` returns ipaddress.IPv4Network object"""
        output = validators.to_network('192.168.1.1', netmask='255.255.255.0')
        expected = validators.ipaddress.IPv4Network('192.168.1.0/24')

        self.assertEqual(output, expected)

    def test_validate_ip_range_ok(self):
        """``validate_ip_range`` - returns None when ip_high bigger than ip_low"""
        output = validators.validate_ip_range(ip_low='1.1.1.1', ip_high='2.2.2.2', group='internal network')
        expected = None

        self.assertEqual(output, expected)

    def test_validate_ip_range_raises(self):
        """``validate_ip_range`` - Raises ValueError when ip_low bigger than ip_high"""
        with self.assertRaises(ValueError):
            validators.validate_ip_range(ip_low='8.1.1.1', ip_high='2.2.2.2', group='internal network')

    def test_validate_ext_network(self):
        """``validate_ext_network`` returns None when network is valid"""
        output = validators.validate_ext_network(netmask='255.255.255.0',
                                                 ext_ip_low='192.168.1.20',
                                                 ext_ip_high='192.168.1.30',
                                                 smartconnect_ip='192.168.1.31',
                                                 gateway='192.168.1.1')
        expected = None

        self.assertEqual(output, expected)

    def test_validate_ext_network_smartconnect_ip_optional(self):
        """``validate_ext_network`` the smartconnect_ip param is optional"""
        output = validators.validate_ext_network(netmask='255.255.255.0',
                                                 ext_ip_low='192.168.1.20',
                                                 ext_ip_high='192.168.1.30',
                                                 smartconnect_ip='',
                                                 gateway='192.168.1.1')
        expected = None

        self.assertEqual(output, expected)

    def test_validate_ext_network_bad_network(self):
        """``validate_ext_network`` raises ValueError if the gateway and mask are junk"""
        with self.assertRaises(ValueError):
            validators.validate_ext_network(netmask='255.253.255.0',
                                            ext_ip_low='192.168.1.20',
                                            ext_ip_high='192.168.1.30',
                                            smartconnect_ip='192.168.1.31',
                                            gateway='192.1.1.1')

    def test_validate_ext_network_bad_ext_low(self):
        """``validate_ext_network`` raises ValueError if ext_low is not in the network"""
        with self.assertRaises(ValueError):
            validators.validate_ext_network(netmask='255.255.255.0',
                                       ext_ip_low='192.1.1.20',
                                       ext_ip_high='192.168.1.30',
                                       smartconnect_ip='192.168.1.31',
                                       gateway='192.168.1.1')

    def test_validate_ext_network_bad_ext_high(self):
        """``validate_ext_network`` raises ValueError if ext_high is not in the network"""
        with self.assertRaises(ValueError):
            validators.validate_ext_network(netmask='255.255.255.0',
                                            ext_ip_low='192.168.1.20',
                                            ext_ip_high='192.1.1.30',
                                            smartconnect_ip='192.168.1.31',
                                            gateway='192.168.1.1')

    def test_validate_ext_network_bad_smartconnect_ip(self):
        """``validate_ext_network`` raises ValueError if smartconnect_ip is not in the network"""
        with self.assertRaises(ValueError):
            validators.validate_ext_network(netmask='255.255.255.0',
                                            ext_ip_low='192.168.1.20',
                                            ext_ip_high='192.168.1.30',
                                            smartconnect_ip='192.1.1.31',
                                            gateway='192.168.1.1')

    def test_validate_names(self):
        """``validate_names`` returns None upon success"""
        output = validators.validate_names('mycluster', group='cluster name')
        expected = None

        self.assertEqual(output, expected)

    def test_validate_names_too_long(self):
        """``validate_names`` raises ValueError if the hostname is too long"""
        with self.assertRaises(ValueError):
            validators.validate_names('-'.join(['a' for x in range(300)]),
                                      group='cluster name')

    def test_validate_names_too_short(self):
        """``validate_names`` raises ValueError if the hostname is too short"""
        with self.assertRaises(ValueError):
            validators.validate_names(hostname='',
                                      group='cluster name')

    def test_validate_names_bad_name(self):
        """``validate_names`` raises ValueError if the hostname contains invalid chars"""
        with self.assertRaises(ValueError):
            validators.validate_names(hostname='1sdf.foo', group='cluster name')

    def test_validate_names_bad_char(self):
        """``validate_names`` raises ValueError if the hostname contains invalid chars"""
        with self.assertRaises(ValueError):
            validators.validate_names(hostname='sdf.foo_bar.com', group='cluster name')

    def test_validate_names_not_alpha(self):
        """``validate_names`` raises ValueError if the hostname does not start with a letter"""
        with self.assertRaises(ValueError):
            validators.validate_names(hostname='-sdf.foo_bar.com', group='cluster name')

    def test_validate_ips(self):
        """``validate_ips`` returns None upon success"""
        output = validators.validate_ips('192.168.1.1', '10.7.1.2', group='front end network')
        expected = None

        self.assertEqual(output, expected)

    def test_validate_ips_raises(self):
        """``validate_ips`` raises ValueError if supplied with not an IP address"""
        with self.assertRaises(ValueError):
            validators.validate_ips('a.b.c.d', group='internal network')

    def test_validate_ips_ipv6(self):
        """``validate_ips`` raises ValueError if supplied with an IPv6 address"""
        with self.assertRaises(ValueError):
            validators.validate_ips('dead::beef', group='internal network')

    def test_validate_netmask(self):
        """``validate_netmask`` returns None upon success"""
        output = validators.validate_netmask('255.255.255.0', group='backend network')
        expected = None

        self.assertEqual(output, expected)

    def test_validate_netmask_raises(self):
        """``validate_netmask`` raises ValueError if supplied with an invalid subnet mask"""
        with self.assertRaises(ValueError):
            validators.validate_netmask('255.2.255.0', group='backend network')

    def test_validate_netmask_bit_zero(self):
        """``validate_netmask`` raises ValueError supplied subnet mask starts with bit zero"""
        with self.assertRaises(ValueError):
            validators.validate_netmask('0.2.255.0', group='backend network')

    def test_supplied_config_values_are_valid(self):
        """``supplied_config_values_are_valid`` Returns an empty string upon success"""
        error_msg = validators.supplied_config_values_are_valid(cluster_name='mycluster',
                                                                int_netmask='255.255.255.0',
                                                                int_ip_low='2.2.2.1',
                                                                int_ip_high='2.2.2.10',
                                                                ext_netmask='255.255.255.0',
                                                                ext_ip_low='10.1.1.2',
                                                                ext_ip_high='10.1.1.20',
                                                                dns_servers='1.1.1.1,8.8.8.8',
                                                                sc_zonename='myzone.foo.com',
                                                                smartconnect_ip='10.1.1.21',
                                                                gateway='10.1.1.1',
                                                                join_cluster=False)
        expected = ''
        self.assertEqual(error_msg, expected)

    def test_supplied_config_values_are_valid_join(self):
        """``supplied_config_values_are_valid`` Can successfully parse required values for a node to join a cluster"""
        error_msg = validators.supplied_config_values_are_valid(cluster_name='mycluster',
                                                                int_netmask='',
                                                                int_ip_low='',
                                                                int_ip_high='',
                                                                ext_netmask='',
                                                                ext_ip_low='',
                                                                ext_ip_high='',
                                                                dns_servers='',
                                                                sc_zonename='',
                                                                smartconnect_ip='',
                                                                gateway='',
                                                                join_cluster=True)
        expected = ''
        self.assertEqual(error_msg, expected)

    def test_supplied_config_values_are_valid_join_error(self):
        """``supplied_config_values_are_valid`` Returns an error message if the join_cluster values are bad"""
        error_msg = validators.supplied_config_values_are_valid(cluster_name='my_cluster',
                                                                int_netmask='',
                                                                int_ip_low='',
                                                                int_ip_high='',
                                                                ext_netmask='',
                                                                ext_ip_low='',
                                                                ext_ip_high='',
                                                                dns_servers='',
                                                                sc_zonename='',
                                                                smartconnect_ip='',
                                                                gateway='',
                                                                join_cluster=True)
        expected = 'Invalid name of my_cluster supplied for cluster name'
        self.assertEqual(error_msg, expected)

    def test_supplied_config_values_are_valid_bad_value(self):
        """``supplied_config_values_are_valid`` Returns an error message if any input is invalid"""
        error_msg = validators.supplied_config_values_are_valid(cluster_name='mycluster',
                                                                int_netmask='255.255.255.0',
                                                                int_ip_low='2.2.3.1',
                                                                int_ip_high='2.2.2.10',
                                                                ext_netmask='255.255.255.0',
                                                                ext_ip_low='10.1.1.2',
                                                                ext_ip_high='10.1.1.20',
                                                                dns_servers='1.1.1.1,8.8.8.8',
                                                                sc_zonename='myzone.foo.com',
                                                                smartconnect_ip='10.1.1.21',
                                                                gateway='10.1.1.1',
                                                                join_cluster=False)
        expected = 'IP 2.2.3.1 larger than top of IP range 2.2.2.10 for the internal network'
        self.assertEqual(error_msg, expected)

if __name__ == '__main__':
    unittest.main()
