# -*- coding: UTF-8 -*-
"""Business logic for backend worker tasks"""
import time
import random
import os.path
from celery.utils.log import get_task_logger
from vlab_inf_common.vmware import vCenter, Ova, vim, virtual_machine, consume_task

from vlab_onefs_api.lib import const


logger = get_task_logger(__name__)
logger.setLevel(const.VLAB_ONEFS_LOG_LEVEL.upper())


def show_onefs(username):
    """Obtain basic information about onefs

    :Returns: Dictionary

    :param username: The user requesting info about their onefs
    :type username: String
    """
    info = {}
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        onefs_vms = {}
        for vm in folder.childEntity:
            info = virtual_machine.get_info(vcenter, vm)
            kind, version = info['note'].split('=')
            if kind == 'OneFS':
                onefs_vms[vm.name] = info
    return onefs_vms


def delete_onefs(username, machine_name):
    """Unregister and destroy a user's onefs node

    :Returns: None

    :param username: The user who wants to delete their jumpbox
    :type username: String

    :param machine_name: The name of the VM to delete
    :type machine_name: String
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for entity in folder.childEntity:
            if entity.name == machine_name:
                info = virtual_machine.get_info(vcenter, entity)
                kind, version = info['note'].split('=')
                if kind == 'OneFS':
                    logger.debug('powering off VM')
                    virtual_machine.power(entity, state='off')
                    delete_task = entity.Destroy_Task()
                    logger.debug('blocking while VM is being destroyed')
                    consume_task(delete_task)
                    break
        else:
            raise ValueError('No OneFS node named {} found'.format(machine_name))


def create_onefs(username, machine_name, image, front_end, back_end):
    """Deploy a OneFS node

    :Returns: Dictionary

    :param username: The user who wants to delete their jumpbox
    :type username: String

    :param machine_name: The name of the OneFS node
    :type machine_name: String

    :param image: The version/image of the OneFS node to create
    :type image: String

    :param front_end: The network to hook up the external network to
    :type front_end: String

    :param back_end: The network to hook the internal network to
    :type back_end: String
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        ova_name = convert_name(image)
        ova = Ova(os.path.join(const.VLAB_ONEFS_IMAGES_DIR, ova_name))
        try:
            network_map = make_network_map(vcenter.networks, front_end, back_end)
            the_vm = virtual_machine.deploy_from_ova(vcenter=vcenter,
                                                     ova=ova,
                                                     network_map=network_map,
                                                     username=username,
                                                     machine_name=machine_name,
                                                     logger=logger)
        finally:
            ova.close()
        spec = vim.vm.ConfigSpec()
        spec.annotation = 'OneFS={}'.format(image)
        task = the_vm.ReconfigVM_Task(spec)
        consume_task(task)
        info = virtual_machine.get_info(vcenter, the_vm)
        return {the_vm.name: info}

def list_images():
    """Obtain a list of available version of OneFS nodes that can be created

    :Returns: List
    """
    images = os.listdir(const.VLAB_ONEFS_IMAGES_DIR)
    images = [convert_name(x, to_version=True) for x in images]
    return images


def convert_name(name, to_version=False):
    """This function centralizes converting between the name of the OVA, and the
    version of software it contains.

    OneFS OVAs follow the naming convention of <VERSION>.ova

    :param name: The thing to covert
    :type name: String

    :param to_version: Set to True to covert the name of an OVA to the version
    :type to_version: Boolean
    """
    if to_version:
        return name.rstrip('.ova')
    else:
        return '{}.ova'.format(name)


def make_network_map(vcenter_networks, front_end, back_end):
    """Define which NICs on the OVA connect to which networks in vCenter

    :Returns: List

    :Raises: ValueError

    :param vcenter_networks: The available networks in vCenter
    :type vcenter_networks: Dictionary

    :param username: The name of the person creating a OneFS node
    :type username: String
    """
    net_map = []
    mapping = [('hostonly', back_end),
               ('nat', front_end),
               ('bridged', back_end)]
    for ova_network, vlab_network in mapping:
        map = vim.OvfManager.NetworkMapping()
        map.name = ova_network
        try:
            map.network = vcenter_networks[vlab_network]
        except KeyError:
            error = 'No network named {}'.format(vlab_network)
            raise ValueError(error)
        net_map.append(map)
    return net_map
