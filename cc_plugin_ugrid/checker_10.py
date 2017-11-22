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
        self.node_dim = None
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
            # verify that the node coordinates' dimensions are equivalent
            node_coord = n
            try:
                for ncoord in ncs:
                    assert ds[ncoord].dimensions == ds[node_coord].dimensions
            except AssertionError:
                # names are not equivalent
                m = 'node_coordinate values must match dimensions in all' +
                    ' variables in which they are defined'
                messages.append(m)
            else:
                self.node_dim = ds[ncoord].dimensions[0]
                score += 1

        return self.make_result(level, score, out_of, desc, messages)

    def check_edge_coordinates_exist(self, ds):
        """
        Checks if the edge coordinates exist as attributes and as variables.
        """
        level = BaseCheck.MEDIUM  # NOTE: is this the correct level I want?
        score = 0
        out_of = 1
        messages = []
        desc = 'mesh\'s edge coordinates are optional variables'

        # no dependencies -- optional variable for all dimensions
        try:
            mesh = ds.get_variables_by_attributes(cf_role='mesh_topology')[0]
            ecs =  mesh.edge_coordinates.split(' ')
            for ec in ecs:
                assert ec in ds.variables
        except IndexError:
            # no grid variable -- skip test (larger issues)
            return None
        except AttributeError:
            # No attribute for edge_coordinates -- let the tester know
            m = '"edge_coordinates" are an optional variable for a dataset of\
                 this dimension; you may want to consider including them.'
            messages.append(m)
        except AssertionError:
            m = '"edge_coordinates" member "{}" is not a variable'
            messages.append(m)
        else:
            score += 1

        return self.make_result(level, score, out_of, desc, messages)


    def check_connectivity(self, ds):
        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'mesh\'s appropriate *_connectivity attribute must exist and' + \
               'variable must be present'

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
            self.connectivity = v
            # we make the assumption that nfaces is the last element of nv dims
            # and that those dimensions are in standard order
            self.assumed_face_dim = ds.variables[self.connectivity].dimensions[-1]

        return self.make_result(level, score, out_of, desc, messages)


    def check_face_dimension(self, ds):
        """
        Checks if the face_dimension attribute exists. This optional attribute
        should be present if the dimensions of connectivity are listed in
        'non-standard' order.
        """

        level = BaseCheck.MEDIUM
        score = 0
        out_of = 1
        messages = []
        desc = 'face_dimension optional in non-standard order.'
        # DEPENDENCIES
        # Skip if check_connectivity fails
        dep = self.check_connectivity(ds)
        if not dep or dep.value[0] != dep.value[1]:
            self.face_dim = None
            return None
        try:
            mesh = ds.get_variables_by_attributes(cf_role='mesh_topology')[0]
            topology_dimension = mesh.topology_dimension
            if topology_dimension == 1:
                # Skip if topolgy dimension < 2
                return None
            elif topology_dimension >= 2:
                assert bool(mesh.face_dimension)
                score += 1
                self.face_dim = ds.dimensions[mesh.face_dimension]
        except AttributeError:
            # not in the dataset -- pass because it's optional
            score += 1
            self.face_dim = self.assumed_face_dim
        return self.make_result(level, score, out_of, desc, messages)


    def check_edge_dimension(self, ds):
        """
        Checks if the edge_dimension attribute exists. This optional attribute
        should be present if the dimensions of connectivity are listed in
        'non-standard' order.
        """

        level = BaseCheck.MEDIUM
        score = 0
        out_of = 1
        messages = []
        desc = 'edge_dimension optional in non-standard order.'
        # DEPENDENCIES
        # Skip if check_connectivity fails
        dep = self.check_connectivity(ds)
        if not dep or dep.value[0] != dep.value[1]:
            return None
        try:
            mesh = ds.get_variables_by_attributes(cf_role='mesh_topology')[0]
            topology_dimension = mesh.topology_dimension
            if topology_dimension == 1:
                # Skip if topolgy dimension < 2
                return None
            elif topology_dimension >= 2:
                assert bool(mesh.edge_dimension)
                self.nedges = ds.dimensions[mesh.edge_dimension]
                score += 1
        except KeyError:
            # ds.dimensions does not have an edge dimension of that name
            m = 'The dataset has "edge_dimension" variable defined,' + \
                ' but no dimension of the same name exists.'
        except AttributeError:
            # not in the dataset -- pass because it's optional
            score += 1
        return self.make_result(level, score, out_of, desc, messages)


    def check_face_coordinates(self, ds):
        """
        Checks if the face_coordinates variable exists. face_coordinates is
        an optional attribute so the only way it should be able to fail is if
        its values do not match with nfaces.

        "These auxiliary coordinate variables will have length nFaces and
        nEdges respectively"

        examples
        --------
        face_coordinates = 'Mesh2_face_x Mesh2_face_y'
        """

        level = BaseCheck.MEDIUM
        score = 0
        out_of = 1
        messages = []
        desc = 'Optional attribute pointing to the the auxiliary coordinate' + \
                ' variables associated with the location of faces and edges'

        dep = self.check_connectivity(ds)
        if not dep or dep.value[0] != dep.value[1]:
            # Skip if no connectivity
            return None
        dep = self.check_face_dimension(ds)
        if not dep or dep.value[0] != dep.value[1]:
            # Skip if no face dimension
            return None

        try:
            mesh = ds.get_variables_by_attributes(cf_role='mesh_topology')[0]
            if mesh.topology_dimension >= 2:
                face_coords = mesh.face_coordinates
                # split and get first element, accessed through variables
                mesh_faces = ds.dimensions[ds.variables[face_coords.split(' ')[0]].dimensions[0]]
                assert int(mesh_faces.size) == self.face_dim.size
                score +=1
            else:
                # skip test because a 1-D array won't have face_coordinates
                return None
        except AttributeError:
            # face_coordinates not in mesh; passes check because it's optional
            mesh_faces = None
            score += 1
        except AssertionError:
            # mesh_faces != nfaces
            m = 'It seems that the face_coordinates' + \
                ' attribute does not match face_dimension.'
            messages.append(m)
        if mesh_faces:
            try:
                # does mesh_faces equal the OTHER value of the conn. dims?
                assert int(mesh_faces.size) == ds.variables[self.connectivity].shape[0]
                m = 'face_coordinates seems to match the incorrect dimension' + \
                'of _connectivity.'
                messages.append(m)
            except AssertionError:
                # mesh_faces does not match either dimension of face_dimension
                # face_coordinates should fail
                # do I make face_dimension fail from here?
                m = 'Your face_coordinates does not match either' + \
                    'dimension of your face_dimension attribute.'
                messages.append(m)

        return self.make_result(level, score, out_of, desc, messages)


    def check_location_mesh_in_variables(self, ds):
        """
        Loops through each variable to see if its dimensions contain time,
        nodes, or faces. If so, imlpements a check for a 'location'
        attribute in the variable; fails if it does not exist.
        """

        # DEPENDENCIES
        self.check_face_dimension(ds)
        self.check_node_coordinates_exist(ds)

        level = BaseCheck.MEDIUM
        score = 0
        out_of = 0
        messages = []
        desc = '"location" & "mesh" strongly encouraged for variables with' + \
                ' dimensions "node" or "faces" (elements)'

        # check attributes
        for var in ds.variables:
            dims = ds[var].dimensions
            m = ''
            try:
                assert any(x in dims for x in [self.node_dim, self.face_dim])
                score += 2
                out_of += 2
                if not 'location' in ds[var].ncattrs():
                    m += ' location'
                    score -= 1
                if not 'mesh' in ds[var].ncattrs():
                    m += ' mesh'
                    score -= 1
            except AssertionError:
                # variable doesn't have these dimensions, continue loop
                continue

            if m:
                messages.append(
                    '{} is missing attribute(s): {};'.format(var, m)
                )

        return self.make_result(level, score, out_of, desc, messages)
