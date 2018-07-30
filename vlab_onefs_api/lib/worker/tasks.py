# -*- coding: UTF-8 -*-
"""
Entry point logic for available backend worker tasks
"""
from celery import Celery
from celery.utils.log import get_task_logger

from vlab_onefs_api.lib import const
from vlab_onefs_api.lib.worker import vmware

app = Celery('onefs', backend='rpc://', broker=const.VLAB_MESSAGE_BROKER)
logger = get_task_logger(__name__)
logger.setLevel(const.VLAB_ONEFS_LOG_LEVEL.upper())


@app.task(name='onefs.show')
def show(username):
    """Obtain basic information about onefs

    :Returns: Dictionary

    :param username: The name of the user who wants info about their default gateway
    :type username: String
    """
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


@app.task(name='onefs.create')
def create(username, machine_name, image, front_end, back_end):
    """TODO

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
    """
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        resp['content'] = vmware.create_onefs(username, machine_name, image, front_end, back_end)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    logger.info('Task complete')
    return resp


@app.task(name='onefs.delete')
def delete(username, machine_name):
    """TODO

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new default gateway
    :type username: String

    :param machine_name: The name of the instance of onefs
    :type machine_name: String
    """
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    try:
        vmware.delete_onefs(username, machine_name)
    except ValueError as doh:
        logger.error('Task failed: {}'.format(doh))
        resp['error'] = '{}'.format(doh)
    else:
        logger.info('Task complete')
    return resp


@app.task(name='onefs.image')
def image():
    """TODO

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new default gateway
    :type username: String
    """
    resp = {'content' : {}, 'error': None, 'params': {}}
    logger.info('Task starting')
    resp['content'] = {'image': vmware.list_images()}
    logger.info('Task complete')
    return resp
