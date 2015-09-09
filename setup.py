# -*- coding: utf-8 -*-
from distutils.core import setup

setup(name='freeradiusparser',
      version='0.1',
      description='FreeRADIUS parser for clients.conf',
      author='Cornelius Kölbel',
      author_email='cornelius.koelbel@netknights.it',
      url='https://github.com/privacyidea/freeradiusparser',
      py_modules=['freeradiusparser'],
      install_requires = [
          'pyparsing>=2.0'
      ]
)
