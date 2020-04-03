# -*- coding: UTF-8 -*-
"""Business logic for backend worker tasks"""
import time
import random
import os.path
from vlab_inf_common.vmware import vCenter, Ova, vim, virtual_machine, consume_task

import ujson

from vlab_onefs_api.lib import const


def show_onefs(username):
    """Obtain basic information about onefs

    :Returns: Dictionary

    :param username: The user requesting info about their onefs
    :type username: String
    """
    onefs_vms = {}
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for vm in folder.childEntity:
            info = virtual_machine.get_info(vcenter, vm, username)
            if info['meta']['component'] == 'OneFS':
                onefs_vms[vm.name] = info
    return onefs_vms


def delete_onefs(username, machine_name, logger):
    """Unregister and destroy a user's onefs node

    :Returns: None

    :param username: The user who wants to delete their OneFS node
    :type username: String

    :param machine_name: The name of the VM to delete
    :type machine_name: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for entity in folder.childEntity:
            if entity.name == machine_name:
                info = virtual_machine.get_info(vcenter, entity, username)
                if info['meta']['component'] == 'OneFS':
                    logger.debug('powering off VM')
                    virtual_machine.power(entity, state='off')
                    delete_task = entity.Destroy_Task()
                    logger.debug('blocking while VM is being destroyed')
                    consume_task(delete_task)
                    break
        else:
            raise ValueError('No OneFS node named {} found'.format(machine_name))


def create_onefs(username, machine_name, image, front_end, back_end, ram, cpu_count, logger):
    """Deploy a OneFS node

    :Returns: Dictionary

    :param username: The user who wants to delete a OneFS node
    :type username: String

    :param machine_name: The name of the OneFS node
    :type machine_name: String

    :param image: The version/image of the OneFS node to create
    :type image: String

    :param front_end: The network to hook up the external network to
    :type front_end: String

    :param back_end: The network to hook the internal network to
    :type back_end: String

    :param ram: The number of GB of memory to provision the node with
    :type ram: Integer

    :param cpu_count: The number of CPU cores to allocate to the vOneFS node
    :type cpu_count: Integer

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        ova_name = convert_name(image)
        try:
            ova = Ova(os.path.join(const.VLAB_ONEFS_IMAGES_DIR, ova_name))
        except FileNotFoundError:
            error = 'Invalid version of OneFS: {}'.format(image)
            raise ValueError(error)
        try:
            network_map = make_network_map(vcenter.networks, front_end, back_end)
            the_vm = virtual_machine.deploy_from_ova(vcenter=vcenter,
                                                     ova=ova,
                                                     network_map=network_map,
                                                     username=username,
                                                     machine_name=machine_name,
                                                     logger=logger,
                                                     power_on=False)
        finally:
            ova.close()
        # ram is supplied in GB
        mb_of_ram = ram * 1024
        virtual_machine.adjust_ram(the_vm, mb_of_ram=mb_of_ram)
        virtual_machine.adjust_cpu(the_vm, cpu_count)
        virtual_machine.power(the_vm, state='on')
        meta_data = {'component': 'OneFS',
                     'created': time.time(),
                     'version': image,
                     'configured': False,
                     'generation': 1} # Versioning of the VM itself
        virtual_machine.set_meta(the_vm, meta_data)
        info = virtual_machine.get_info(vcenter, the_vm, username)
        return {the_vm.name: info}


def update_meta(username, vm_name, new_meta):
    """Connect to vSphere and update the VM meta data

    :Returns: None

    :param username: The user who owns the OneFS node
    :type username: String

    :param vm_name: The name of the VM to update the meta data on
    :type vm_name: String

    :param new_meta: The new meta data to overwrite the old meta data with
    :type new_meta: Dictionary
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for vm in folder.childEntity:
            if vm.name == vm_name:
                virtual_machine.set_meta(vm, new_meta)


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



def update_network(username, machine_name, new_network):
    """Implements the VM network update

    :param username: The name of the user who owns the virtual machine
    :type username: String

    :param machine_name: The name of the virtual machine
    :type machine_name: String

    :param new_network: The name of the new network to connect the VM to
    :type new_network: String
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for entity in folder.childEntity:
            if entity.name == machine_name:
                info = virtual_machine.get_info(vcenter, entity, username)
                if info['meta']['component'] == 'OneFS':
                    the_vm = entity
                    break
        else:
            error = 'No VM named {} found'.format(machine_name)
            raise ValueError(error)

        try:
            network = vcenter.networks[new_network]
        except KeyError:
            error = 'No VM named {} found'.format(machine_name)
            raise ValueError(error)
        else:
            # the front-end NIC in vOneFS is the 2nd NIC, for whatever reason...
            virtual_machine.change_network(the_vm, network, adapter_label='Network adapter 2')
