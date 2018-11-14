# -*- coding: UTF-8 -*-
"""This module contains functions for validating user input"""
import re
import ipaddress


def supplied_config_values_are_valid(int_netmask, int_ip_low, int_ip_high, ext_netmask,
                                     ext_ip_low, ext_ip_high, gateway, cluster_name,
                                     sc_zonename, smartconnect_ip, dns_servers, join_cluster):
    """Additional input validation for OneFS config parameters.

    :Returns: String

    :param cluster_name: The name to give the new cluster
    :type cluster_name: String

    :param int_netmask: The subnet mask for the internal OneFS network
    :type int_netmask: String

    :param int_ip_low: The smallest IP to assign to an internal NIC
    :type int_ip_low: String (IPv4 address)

    :param int_ip_high: The largest IP to assign to an internal NIC
    :type int_ip_high: String (IPv4 address)

    :param ext_ip_low: The smallest IP to assign to an external/public NIC
    :type ext_ip_low: String (IPv4 address)

    :param ext_ip_high: The largest IP to assign to an external/public NIC
    :type ext_ip_high: String (IPv4 address)

    :param gateway: The IP address for the default gateway
    :type gateway: String (IPv4 address)

    :param dns_servers: A common separated list of IPs of the DNS servers to use
    :type dns_servers: String

    :param sc_zonename: The SmartConnect Zone name to use. Skipped if None.
    :type sc_zonename: String

    :param smartconnect_ip: The IPv4 address to use as the SIP
    :type smartconnect_ip: String (IPv4 address)

    :param join_cluster: Set to True to only validate input for joining an existing cluster
    :type join_cluster: Boolean
    """
    error = ''
    if join_cluster:
        try:
            validate_names(cluster_name, group='cluster name')
        except ValueError as doh:
            error = str(doh)
    else:
        try:
            validate_netmask(int_netmask, group='internal')
            validate_netmask(ext_netmask, group='external')
            validate_ips(int_ip_low, int_ip_high, group='the internal network')
            validate_ips(ext_ip_low, ext_ip_high, group='the external network')
            validate_ip_range(int_ip_low, int_ip_high, group='the internal network')
            validate_ip_range(ext_ip_low, ext_ip_high, group='the external network')
            for dns_ip in dns_servers.split(','):
                validate_ips(dns_ip, group='DNS')
            if smartconnect_ip:
                validate_ips(smartconnect_ip, group='smartconnect')
            validate_ext_network(ext_netmask, ext_ip_low, ext_ip_high, smartconnect_ip, gateway)
            validate_names(cluster_name, group='cluster name')
            if sc_zonename:
                validate_names(cluster_name, group='SmartConnect Zone name')
        except ValueError as doh:
            error = '{}'.format(doh)
    return error


def validate_netmask(mask, group):
    """Ensure the subnet mask supplied is valid.

    A valid subnet mask will be bit values 1 to define what's "not local." In the
    32 bits that make an IPv4 address, once the mask is defined, only a bit value
    of 0 is valid. I.E. once you go zero, you never go back to one.

    :Returns: None

    :Raises: ValueError
    """
    try:
        octets = [int(x) for x in mask.split('.')]
        last_bit = None
        for octet in octets:
            bits = bin(octet)[2:] # strip of the 0b part...
            for bit in bits:
                if last_bit is None:
                    if bit != '1':
                        raise ValueError('Netmask must begin with bit 1')
                    else:
                        last_bit = bit
                elif (bit != last_bit) and bit == '1':
                    raise ValueError('Netmask cannot contain bit value 1 after zero')
                else:
                    last_bit = bit
    except ValueError:
        error = 'Invalid Subnet {} supplied for the {} network'.format(mask, group)
        raise ValueError(error)


def validate_ips(*args, group=None):
    """Ensure the supplied IPs are IPv4 addresses

    :Returns: None

    :Raises: ValueError
    """
    for ip in args:
        try:
            ipaddress.IPv4Address(ip)
        except ipaddress.AddressValueError:
            error = 'Supplied IP {} is not a valid IPv4 address for {}'.format(ip, group)
            raise ValueError(error)


def validate_names(hostname, group):
    """Ensure the supplied name is a valid hostname https://tools.ietf.org/html/rfc1123

    :Returns: None

    :Raises: ValueError
    """
    ok = True
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    hostname = hostname.rstrip('.') # remove any trailing dot
    try:
        int(hostname[0])
        ok = False # hostname cannot start with a number
    except ValueError:
        if len(hostname) > 253 or len(hostname) < 1:
            ok = False
        elif not all(allowed.match(x) for x in hostname.split(".")):
            ok = False
    if not ok:
        error = 'Invalid name of {} supplied for {}'.format(hostname, group)
        raise ValueError(error)


def validate_ext_network(netmask, ext_ip_low, ext_ip_high, smartconnect_ip, gateway):
    """Ensure the supplied external network subnet and ips are OK

    :Returns: None

    :Raises: ValueError
    """
    error = ''
    # default gateway must within supplied subnet, so lets assume that is the network
    try:
        network = list(to_network(gateway, netmask))
    except Exception:
        error = 'Default gateway {} not part of subnet {}'.format(gateway, netmask)
        raise ValueError(error)
    if not ipaddress.IPv4Address(ext_ip_low) in network:
        error = 'Ext IP {} not part of network {}'.format(ext_ip_low, network)
    elif not ipaddress.IPv4Address(ext_ip_high) in network:
        error = 'Ext IP {} not part of network {}'.format(ext_ip_low, network)
    elif smartconnect_ip:
        # skipping config of SmartConnect is OK
        if not ipaddress.IPv4Address(smartconnect_ip) in network:
            error = 'SmartConnect IP {} not part of network {}'.format(smartconnect_ip, network)
    if error:
        raise ValueError(error)


def validate_ip_range(ip_low, ip_high, group):
    """Ensure the bottom of the IP range comes after the top of the IP range

    :Returns: None

    :Raises: ValueError
    """
    if not ip_low <= ip_high:
        error = 'IP {} larger than top of IP range {} for {}'.format(ip_low, ip_high, group)
        raise ValueError(error)


def to_network(ip, netmask):
    """Convert an IP and subnet mask into CIDR format

    :Returns: ipaddress.IPv4Network
    """
    ipaddr = ip.split('.')
    mask = netmask.split('.')
    # to calculate network start do a bitwise AND of the octets between netmask and ip
    net_start = '.'.join([str(int(ipaddr[x]) & int(mask[x])) for x in range(4)])
    bit_count = sum([bin(int(x)).count("1") for x in netmask.split('.')])
    cidr = '{}/{}'.format(net_start, bit_count)
    return ipaddress.IPv4Network(cidr)
