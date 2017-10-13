#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from cc_plugin_ugrid import UgridChecker, logger
from compliance_checker.base import BaseCheck

class UgridChecker10(UgridChecker):

    _cc_spec_version = '1.0'
    _cc_description = 'UGRID {} compliance-checker'.format(_cc_spec_version)

    METHODS_REGEX = re.compile('(\w+: *\w+) \((\w+: *\w+)\) *')
    PADDING_TYPES = [ "none", "low", "high", "both" ]

    def check_something1(self, ds):
        level = BaseCheck.HIGH
        score = 1
        out_of = 1
        messages = ['passed']
        desc = 'Does something'

        return self.make_result(level, score, out_of, desc, messages)

    def check_mesh_topology_variable(self, ds):
        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'cf_role:mesh_topology variable exists'

        mt = ds.get_variables_by_attributes(cf_role='mesh_topology')
        if len(mt) == 1:
            score += 1
        elif len(mt) > 1:
            m = ('One variable with attribute "cf_role:mesh_topology" allowed')
            messages.append(m)
        elif len(mt) < 1:
            m = ('Variable with attribute "cf_role:mesh_topology" required')
            messages.append(m)

        return self.make_result(level, score, out_of, desc, messages)

    def check_topology_dimension(self, ds):
        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'mesh\'s topology_dimension attribute is 1, 2 or 3'

        try:
            mesh = ds.get_variables_by_attributes(cf_role='mesh_topology')[0]
            assert mesh.topology_dimension in [1, 2, 3]
        except IndexError:
            # No mesh variable, just skip the test... there are larger issues
            return None
        except AttributeError:
            m = ('"topology_dimension" attribute does not exist in mesh')
            messages.append(m)
        except AssertionError:
            m = ('"topology_dimension" attribute must be 1, 2 or 3')
            messages.append(m)
        else:
            score += 1

        return self.make_result(level, score, out_of, desc, messages)

    def check_node_coordinates_size(self, ds):
        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'mesh\'s node_coordinates length is same as topology_dimension'

        # DEPENDENCIES
        # Skip if no topology_dimension
        dep = self.check_topology_dimension(ds)
        if not dep or dep.value[0] != dep.value[1]:
            return None

        try:
            mesh = ds.get_variables_by_attributes(cf_role='mesh_topology')[0]
            ncs = mesh.node_coordinates.split(' ')
            assert len(ncs) == mesh.topology_dimension
        except IndexError:
            # No mesh variable, just skip the test... there are larger issues
            return None
        except AttributeError:
            m = ('"node_coordinates" attribute does not exists on mesh')
            messages.append(m)
        except AssertionError:
            m = ('"node_coordinates" attribute length must equal '
                 '"topology_dimension" value')
            messages.append(m)
        else:
            score += 1

        return self.make_result(level, score, out_of, desc, messages)

    def check_node_coordinates_exist(self, ds):
        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'mesh\'s node_coordinates values must be variables'

        # DEPENDENCIES
        # Skip if node_coordinates_size fails
        dep = self.check_node_coordinates_size(ds)
        if not dep or dep.value[0] != dep.value[1]:
            return None

        try:
            mesh = ds.get_variables_by_attributes(cf_role='mesh_topology')[0]
            ncs = mesh.node_coordinates.split(' ')
            for n in ncs:
                assert n in ds.variables
        except IndexError:
            # No grid variable, just skip the test... there are larger issues
            return None
        except AttributeError:
            # No node_dimensions attribute... there are larger issues
            return None
        except AssertionError:
            m = '"node_coordinates" member "{}" is not a variable'.format(n)
            messages.append(m)
        else:
            score += 1

        return self.make_result(level, score, out_of, desc, messages)

    def check_connectivity(self, ds):
        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'mesh\'s appropriate *_connectivity attribute must exist'

        # DEPENDENCIES
        # Skip if no topology_dimension
        dep = self.check_topology_dimension(ds)
        if not dep or dep.value[0] != dep.value[1]:
            return None

        try:
            mesh = ds.get_variables_by_attributes(cf_role='mesh_topology')[0]
            topology_dimension = mesh.topology_dimension
            if topology_dimension == 1:
                c = 'edge_node_connectivity'
            elif topology_dimension == 2:
                c = 'face_node_connectivity'
            elif topology_dimension == 3:
                c = 'volume_node_connectivity'
            else:
                c = 'FAIL' # should never happen
            v = mesh.getncattr(c)
            assert v in ds.variables
        except IndexError:
            # No mesh variable, just skip the test... there are larger issues
            return None
        except AttributeError:
            m = '"{}" attribute does not exist in mesh'.format(c)
            messages.append(m)
        except AssertionError:
            m = '"{}" value "{}" is not a variable'.format(c, v)
            messages.append(m)
        else:
            score += 1

        return self.make_result(level, score, out_of, desc, messages)
