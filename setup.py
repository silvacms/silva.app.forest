# -*- coding: utf-8 -*-
# Copyright (c) 2002-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from setuptools import setup, find_packages
import os

version = '1.0dev'

tests_require = [
    'Products.Silva [testing]',
    ]

setup(name='silva.app.forest',
      version=version,
      description="Advanced virtual hosting for Silva",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Zope2",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='silva advanced virtual hosting rewrite rules',
      author='Infrae',
      author_email='info@infrae.com',
      url='http://infrae.com/products/silva',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['silva', 'silva.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'Zope2',
        'five.grok',
        'infrae.wsgi >= 2.0a1',
        ],
      tests_require=tests_require,
      extras_require={'test': tests_require},
      )
