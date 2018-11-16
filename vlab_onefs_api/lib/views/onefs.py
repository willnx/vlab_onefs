# -*- coding: UTF-8 -*-
"""
Defines the RESTful HTTP API for the OneFS service
"""
import re
import ipaddress
from socket import inet_aton

import ujson
from flask import current_app
from flask_classy import request, route, Response
from vlab_inf_common.views import TaskView
from vlab_inf_common.vmware import vCenter, vim
from vlab_api_common import describe, get_logger, requires, validate_input


from vlab_onefs_api.lib import const
from vlab_onefs_api.lib.validators import supplied_config_values_are_valid


logger = get_logger(__name__, loglevel=const.VLAB_ONEFS_LOG_LEVEL)


class OneFSView(TaskView):
    """API end point TODO"""
    route_base = '/api/1/inf/onefs'
    POST_SCHEMA = { "$schema": "http://json-schema.org/draft-04/schema#",
                    "type": "object",
                    "description": "Create a new vOneFS node",
                    "properties": {
                        "name": {
                            "description": "The unique name to give your OneFS node",
                            "type": "string"
                        },
                        "image": {
                            "description": "The specific image/version of OneFS to create",
                            "type": "string"
                        },
                        "frontend": {
                            "description": "The front end (aka public) network to use",
                            "type": "string"
                        },
                        "backend": {
                            "description": "The back end (aka private) network to use",
                            "type": "string"
                        }
                    },
                    "required": ["name", 'image', 'frontend', 'backend']
                  }

    DELETE_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                     "description": "Destroy a vOneFS node",
                     "type": "object",
                     "properties": {
                        "name": {
                            "description": "The name of the OneFS node to destroy",
                            "type": "string"
                        }
                     },
                     "required": ["name"]
                    }

    GET_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                  "description": "Display the vOneFS nodes you own"
                 }

    IMAGES_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                     "description": "View available versions of vOneFS that can be created"
                    }
    CONFIG_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                     "description": "Configure a OneFS node",
                     "type": "object",
                     "properties": {
                        "cluster_name": {
                            "description": "The name of the OneFS cluster to create/join",
                            "type": "string"
                        },
                        "name": {
                            "description" : "The name of the OneFS node to configure",
                            "type": "string"
                        },
                        "join": {
                            "description": "Join node to an existing cluster",
                            "type": "boolean"
                        },
                        "version" : {
                            "description" : "The version of OneFS being configured (the config wizard changes with versions)",
                            "type": "string"
                        },
                        "ext_ip_high": {
                            "description": "The top of the IP range of the external network to allocate to the cluster",
                            "type": "string"
                        },
                        "ext_ip_low": {
                            "description": "The bottom of the IP range of the external network to allocate to the cluster",
                            "type": "string"
                        },
                        "ext_netmask": {
                            "description": "The subnet mask to give the external network",
                            "type": "string"
                        },
                        "int_ip_high": {
                            "description": "The top of the IP range of the internal network to allocate to the cluster",
                            "type": "string"
                        },
                        "int_ip_low": {
                            "description": "The bottom of the IP range of the internal network to allocate to the cluster",
                            "type": "string"
                        },
                        "int_netmask": {
                            "description": "The subnet mask to give the internal network",
                            "type": "string"
                        },
                        "gateway": {
                            "description": "The default gateway to use on the external network",
                            "type": "string"
                        },
                        "dns_servers": {
                            "description": "The DNS servers to configure on the EXT network",
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "sc_zonename": {
                            "description": "The name of the SmartConnect Zone name. Empty string is valid",
                            "type": "string"
                        },
                        "smartconnect_ip": {
                            "description": "The SIP to configure on the external network. Empty string is valid",
                            "type": "string"
                        },
                        "encoding": {
                            "description": "The filesystem encoding to use.",
                            "type": "string",
                            "enum": ['windows-sjis', 'windows-949', 'windows-1252',
                                     'euc-kr', 'euc-jp', 'euc-jp-ms', 'utf-8-mac',
                                     'utf-8', 'latin-1', 'latin-2', 'latin-3',
                                     'latin-4', 'cyrillic', 'arabic', 'greek',
                                     'hebrew', 'latin-5', 'latin-6', 'latin-7',
                                     'latin-8', 'latin-9', 'latin-10']
                        }

                     },
                     "oneOf": [
                        {"required": ["name", "cluster_name", "join"],
                         "not": {"required": ["ext_ip_high", "ext_ip_low", "ext_netmask",
                                              "int_ip_high", "int_ip_low", "int_netmask",
                                              "dns_servers", "sc_zonename", "smartconnect_ip",
                                              "encoding", "version", "gateway"
                                              ]
                                }
                        },
                        {"required": ["name", "cluster_name", "encoding", "version",
                                      "ext_ip_high","ext_ip_low", "ext_netmask",
                                      "int_ip_high", "int_ip_low", "int_netmask",
                                      "dns_servers", "sc_zonename", "smartconnect_ip",
                                      "gateway"
                                      ],
                         "not": {"required": ["join"]}
                        }
                     ]
                    }

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=(1,2))
    @describe(post=POST_SCHEMA, delete=DELETE_SCHEMA, get_args=GET_SCHEMA)
    def get(self, *args, **kwargs):
        """Display the vOneFS nodes you own"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        task = current_app.celery_app.send_task('onefs.show', [username])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=(1,2)) # XXX remove verify=False before commit
    @validate_input(schema=POST_SCHEMA)
    def post(self, *args, **kwargs):
        """Create a new vOneFS node"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        body = kwargs['body']
        machine_name = body['name']
        image = body['image']
        front_end = body['frontend']
        back_end = body['backend']
        task = current_app.celery_app.send_task('onefs.create', [username, machine_name, image, front_end, back_end])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        resp.headers.add('Link', '<{0}{1}/config>; rel=config>'.format(const.VLAB_URL, self.route_base))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=(1,2)) # XXX remove verify=False before commit
    @validate_input(schema=DELETE_SCHEMA)
    def delete(self, *args, **kwargs):
        """Destroy a vOneFS node"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        machine_name = kwargs['body']['name']
        task = current_app.celery_app.send_task('onefs.delete', [username, machine_name])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @route('/image', methods=["GET"])
    @requires(verify=const.VLAB_VERIFY_TOKEN, version=(1,2))
    @describe(get=IMAGES_SCHEMA)
    def image(self, *args, **kwargs):
        """Show available versions of OneFS that can be deployed"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        task = current_app.celery_app.send_task('onefs.image')
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @route('/config', methods=["POST"])
    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @describe(post=CONFIG_SCHEMA)
    @validate_input(schema=CONFIG_SCHEMA)
    def config(self, *args, **kwargs):
        """Set the configuration of a OneFS node"""
        status_code = 202
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        # Aligning these just makes it easier to read
        cluster_name    = kwargs['body']['cluster_name']
        name            = kwargs['body']['name']
        version         = kwargs['body'].get('version', None)
        int_netmask     = kwargs['body'].get('int_netmask', None)
        int_ip_low      = kwargs['body'].get('int_ip_low', None)
        int_ip_high     = kwargs['body'].get('int_ip_high', None)
        ext_netmask     = kwargs['body'].get('ext_netmask', None)
        ext_ip_low      = kwargs['body'].get('ext_ip_low', None)
        ext_ip_high     = kwargs['body'].get('ext_ip_high', None)
        gateway         = kwargs['body'].get('gateway', None)
        encoding        = kwargs['body'].get('encoding', None)
        sc_zonename     = kwargs['body'].get('sc_zonename', None)
        smartconnect_ip = kwargs['body'].get('smartconnect_ip', None)
        join_cluster    = kwargs['body'].get('join', False)
        dns_servers     = ','.join(kwargs['body'].get('dns_servers', []))
        # Ensure supplied values wont generate an error in the OneFS config wizard
        error = supplied_config_values_are_valid(int_netmask=int_netmask,
                                                 int_ip_low=int_ip_low,
                                                 int_ip_high=int_ip_high,
                                                 ext_netmask=ext_netmask,
                                                 ext_ip_low=ext_ip_low,
                                                 ext_ip_high=ext_ip_high,
                                                 gateway=gateway,
                                                 cluster_name=cluster_name,
                                                 sc_zonename=sc_zonename,
                                                 smartconnect_ip=smartconnect_ip,
                                                 dns_servers=dns_servers,
                                                 join_cluster=join_cluster)
        if error:
            resp_data['error'] = error
            status_code = 400
            link = None
        else:
            task = current_app.celery_app.send_task('onefs.config', kwargs={'cluster_name' : cluster_name,
                                                                            'name' : name,
                                                                            'username' : username,
                                                                            'version' : version,
                                                                            'int_netmask' : int_netmask,
                                                                            'int_ip_low' : int_ip_low,
                                                                            'int_ip_high' : int_ip_high,
                                                                            'ext_netmask' : ext_netmask,
                                                                            'ext_ip_low' : ext_ip_low,
                                                                            'ext_ip_high' : ext_ip_high,
                                                                            'gateway' : gateway,
                                                                            'dns_servers' : dns_servers,
                                                                            'encoding' : encoding,
                                                                            'sc_zonename' : sc_zonename,
                                                                            'smartconnect_ip' : smartconnect_ip,
                                                                            'join_cluster' : join_cluster})

            resp_data['content'] = {'task-id': task.id}
            link = '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id)
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = status_code
        if link:
            resp.headers.add('Link', link)
        return resp
