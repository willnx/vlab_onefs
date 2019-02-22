#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
RESTful API for creating vOneFS nodes
"""
from setuptools import setup, find_packages


setup(name="vlab-onefs-api",
      author="Nicholas Willhite,",
      author_email='willnx84@gmail.com',
      version='2019.02.22',
      packages=find_packages(),
      include_package_data=True,
      package_files={'vlab_onefs_api' : ['app.ini']},
      description="Deploy vOneFS nodes in your vLab",
      install_requires=['flask', 'ldap3', 'pyjwt', 'uwsgi', 'vlab-api-common',
                        'ujson', 'cryptography', 'vlab-inf-common', 'celery',
                        'selenium']
      )
