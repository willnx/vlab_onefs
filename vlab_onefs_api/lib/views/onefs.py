# -*- coding: UTF-8 -*-
"""
Defines the RESTful HTTP API for the OneFS service
"""
import ujson
from flask import current_app
from flask_classy import request, route
from vlab_inf_common.views import TaskView
from vlab_inf_common.vmware import vCenter, vim
from vlab_api_common import describe, get_logger, requires, validate_input


from vlab_onefs_api.lib import const


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

    @requires(verify=False)
    @describe(post=POST_SCHEMA, delete=DELETE_SCHEMA, get_args=GET_SCHEMA)
    def get(self, *args, **kwargs):
        """Display the vOneFS nodes you own"""
        username = kwargs['token']['username']
        resp = {'user' : username}
        task = current_app.celery_app.send_task('onefs.show', [username])
        resp['content'] = {'task-id': task.id}
        return ujson.dumps(resp), 200

    @requires(verify=False) # XXX remove verify=False before commit
    @validate_input(schema=POST_SCHEMA)
    def post(self, *args, **kwargs):
        """Create a new vOneFS node"""
        username = kwargs['token']['username']
        resp = {'user' : username}
        body = kwargs['body']
        machine_name = body['name']
        image = body['image']
        front_end = body['frontend']
        back_end = body['backend']
        task = current_app.celery_app.send_task('onefs.create', [username, machine_name, image, front_end, back_end])
        resp['content'] = {'task-id': task.id}
        return ujson.dumps(resp), 200

    @requires(verify=False) # XXX remove verify=False before commit
    @validate_input(schema=DELETE_SCHEMA)
    def delete(self, *args, **kwargs):
        """Destroy a vOneFS node"""
        username = kwargs['token']['username']
        resp = {'user' : username}
        machine_name = kwargs['body']['name']
        task = current_app.celery_app.send_task('onefs.delete', [username, machine_name])
        resp['content'] = {'task-id': task.id}
        return ujson.dumps(resp), 200

    @route('/image', methods=["GET"])
    @requires(verify=False)
    @describe(get=IMAGES_SCHEMA)
    def image(self, *args, **kwargs):
        """Show available versions of OneFS that can be deployed"""
        username = kwargs['token']['username']
        resp = {'user' : username}
        task = current_app.celery_app.send_task('onefs.image')
        resp['content'] = {'task-id': task.id}
        return ujson.dumps(resp), 200
