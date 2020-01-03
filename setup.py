# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(name='freeradiusparser',
      packages=find_packages(),
      version='0.2',
      description='FreeRADIUS parser for clients.conf',
      author='Cornelius Kölbel',
      author_email='cornelius.koelbel@netknights.it',
      url='https://github.com/privacyidea/freeradiusparser',
      py_modules=['freeradiusparser'],
      install_requires=[
            'pyparsing>=2.0',
            'six'
      ],
      )
