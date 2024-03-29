# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from setuptools import setup, find_packages
import os

version = '3.0.2dev'

tests_require = [
    'Products.Silva [test]',
    'silvatheme.standardissue',
    'silvatheme.multiflex',
    ]

setup(name='silva.app.forest',
      version=version,
      description="Advanced virtual hosting for Silva CMS",
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
      url='https://github.com/silvacms/silva.app.forest',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['silva', 'silva.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'five.grok',
        'infrae.wsgi',
        'setuptools',
        'silva.core.conf',
        'silva.core.interfaces',
        'silva.core.layout',
        'silva.core.services',
        'silva.core.views',
        'silva.translations',
        'zeam.form.silva',
        'zope.component',
        'zope.interface',
        'zope.publisher',
        'zope.schema',
        ],
      tests_require=tests_require,
      extras_require={'test': tests_require},
      )
