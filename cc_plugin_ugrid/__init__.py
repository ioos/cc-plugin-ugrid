#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from compliance_checker.base import BaseNCCheck, Result

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class UgridException(Exception):
    pass

class UgridChecker(BaseNCCheck):
    _cc_spec = 'UGRID'
    _cc_url = 'https://github.com/ioos/cc-plugin-ugrid'
    _cc_author = 'Brian McKenna <brian.mckenna@rpsgroup.com>'
    _cc_checker_version = __version__

    @classmethod
    def beliefs(cls): 
        return {}

    @classmethod
    def make_result(cls, level, score, out_of, name, messages):
        return Result(level, (score, out_of), name, messages)

    def setup(self, ds):
        pass
