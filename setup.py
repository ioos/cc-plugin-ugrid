#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from setuptools import setup, find_packages

import versioneer


def readme():
    with open('README.md') as f:
        return f.read()


reqs = [line.strip() for line in open('requirements.txt')]

setup(
    name                 = "cc-plugin-ugrid",
    version              = versioneer.get_version(),
    description          = "UGRID plugin for the IOOS Compliance Checker Plugin",
    long_description     = readme(),
    license              = 'Apache License 2.0',
    author               = "Brian McKenna",
    author_email         = "brian.mckenna@rpsgroup.com",
    url                  = "https://github.com/ioos/cc-plugin-ugrid",
    packages             = find_packages(),
    install_requires     = reqs,
    classifiers          = [
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python',
            'Topic :: Scientific/Engineering'
        ],
    entry_points         = {
        'compliance_checker.suites': [
            'ugrid = cc_plugin_ugrid.checker:UgridChecker',
        ],
    },
    cmdclass=versioneer.get_cmdclass(),
)
