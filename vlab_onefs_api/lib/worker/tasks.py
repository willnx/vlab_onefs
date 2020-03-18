# -*- coding: UTF-8 -*-
"""
Entry point logic for available backend worker tasks
"""
from celery import Celery
from vlab_api_common import get_task_logger

from vlab_onefs_api.lib import const
from vlab_onefs_api.lib.worker import vmware, setup_onefs

app = Celery('onefs', backend='rpc://', broker=const.VLAB_MESSAGE_BROKER)


@app.task(name='onefs.show', bind=True)
def show(self, username, txn_id):
    """Obtain basic information about onefs

    :Returns: Dictionary

    :param username: The name of the user who wants info about their default gateway
    :type username: String

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_ONEFS_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        info = vmware.show_onefs(username)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    else:
        logger.info('Task complete')
        resp['content'] = info
    return resp


@app.task(name='onefs.create', bind=True)
def create(self, username, machine_name, image, front_end, back_end, ram, txn_id):
    """Deploy a new OneFS node

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new default gateway
    :type username: String

    :param machine_name: The name of the new OneFS node
    :type machine_name: String

    :param image: The image version of OneFS to create
    :type image: String

    :param front_end: The network to hook up the external network to
    :type front_end: String

    :param back_end: The network to hook the internal network to
    :type back_end: String

    :param ram: The number of GB of memory to provision the node with
    :type ram: Integer

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_ONEFS_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        resp['content'] = vmware.create_onefs(username, machine_name, image, front_end, back_end, ram, logger)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    logger.info('Task complete')
    return resp


@app.task(name='onefs.delete', bind=True)
def delete(self, username, machine_name, txn_id):
    """Destroy a OneFS node

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new default gateway
    :type username: String

    :param machine_name: The name of the instance of onefs
    :type machine_name: String

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_ONEFS_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        vmware.delete_onefs(username, machine_name, logger)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    else:
        logger.info('Task complete')
    return resp


@app.task(name='onefs.image', bind=True)
def image(self, txn_id):
    """Obtain the available OneFS images/versions that can be deployed

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new default gateway
    :type username: String

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_ONEFS_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    resp['content'] = {'image': vmware.list_images()}
    logger.info('Task complete')
    return resp


@app.task(name='onefs.config', bind=True)
def config(self, cluster_name, name, username, version, int_netmask, int_ip_low,
           int_ip_high, ext_netmask, ext_ip_low, ext_ip_high, gateway, dns_servers,
           encoding, sc_zonename, smartconnect_ip, join_cluster, compliance, txn_id):
    """Turn a blank OneFS node into a usable device

    :Returns: Dictionary

    :param cluster_name: The name of the OneFS cluster
    :type cluster_name: String

    :param name: The name of the OneFS node
    :type name: String

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

    :param encoding: The filesystem encoding to use.
    :type encoding: String

    :param sc_zonename: The SmartConnect Zone name to use. Skipped if None.
    :type sc_zonename: String

    :param smartconnect_ip: The IPv4 address to use as the SIP
    :type smartconnect_ip: String (IPv4 address)

    :param join_cluster: Add the node to an existing cluster
    :type join_cluster: Boolean

    :param compliance: Set to True when creating a Compliance mode cluster
    :type compliance: Boolean

    :param txn_id: A unique string supplied by the client to track the call through logs
    :type txn_id: String
    """
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_ONEFS_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    nodes =  vmware.show_onefs(username)
    node = nodes.get(name, None)
    if not node:
        error = "No node named {} found".format(name)
        resp['error'] = error
        logger.error(error)
        return resp
    elif node['meta']['configured']:
        error = "Cannot configure a node that's already configured"
        resp['error'] = error
        logger.error(error)
    else:
        # Lets set it up!
        logger.info('Found node')
        console_url = node['console']
        if join_cluster:
            logger.info('Joining node to cluster {}'.format(cluster_name))
            setup_onefs.join_existing_cluster(console_url, cluster_name, compliance, logger)
        else:
            logger.info('Setting up new cluster named {}'.format(cluster_name))
            setup_onefs.configure_new_cluster(version=version,
                                              console_url=console_url,
                                              cluster_name=cluster_name,
                                              int_netmask=int_netmask,
                                              int_ip_low=int_ip_low,
                                              int_ip_high=int_ip_high,
                                              ext_netmask=ext_netmask,
                                              ext_ip_low=ext_ip_low,
                                              ext_ip_high=ext_ip_high,
                                              gateway=gateway,
                                              dns_servers=dns_servers,
                                              encoding=encoding,
                                              sc_zonename=sc_zonename,
                                              smartconnect_ip=smartconnect_ip,
                                              compliance=compliance,
                                              logger=logger)
    node['meta']['configured'] = True
    vmware.update_meta(username, name, node['meta'])
    logger.info('Task complete')
    return resp


@app.task(name='onefs.modify_network', bind=True)
def modify_network(self, username, machine_name, new_network, txn_id):
    """Change the network an OneFS node is connected to"""
    logger = get_task_logger(txn_id=txn_id, task_id=self.request.id, loglevel=const.VLAB_ONEFS_LOG_LEVEL.upper())
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        vmware.update_network(username, machine_name, new_network)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    logger.info('Task complete')
    return resp
