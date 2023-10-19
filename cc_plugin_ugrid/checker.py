import re
from cc_plugin_ugrid import UgridChecker 
from compliance_checker.base import BaseCheck


class UgridChecker(UgridChecker):

    _cc_spec_version = '2.0'
    _cc_description = 'UGRID {} compliance-checker'.format(_cc_spec_version)
    _cc_display_headers = {
        3: 'Highly Recommended',
        2: 'Recommended',
        1: 'Suggested'
    }

    METHODS_REGEX = re.compile(r'(\w+: *\w+) \((\w+: *\w+)\) *')
    PADDING_TYPES = [ "none", "low", "high", "both" ]

    def __init__(self):
        pass


    def _check1_topology_dim(self, mesh):
        """
        Check the dimension of the mesh topology is valid.

        :param NetCDF4 variable mesh
        """

        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'The topology dimension is the highest dimension of the data'

        if not self.meshes[mesh]['topology_dimension']:
            m = 'Mesh does not contain the required attribute "topology_dimension"'
            messages.append(m)

        try:
            assert self.meshes[mesh]['topology_dimension'] in [1, 2, 3]
        except AssertionError:
            m = 'Invalid topology_dimension "{}" of type "{}"'.format(
                self.meshes[mesh]['topology_dimension'],
                type(self.meshes[mesh]['topology_dimension']))
            messages.append(m)
        else:
            score += 1

        return self.make_result(level, score, out_of, desc, messages)


    def _check2_connectivity_attrs(self, mesh):
        """
        Check the connecivity attributes of a given mesh. Dependent on
        the existence of topology_dimension attribute. This method is a wrapper
        for the methods which validate the individual connectivity attributes.

        :param NetCDF4 variable mesh

        Notes
        -----
        A mesh's (inter)connectivity is the inter-connection of geometrical
        elements in the mesh. A mesh can distinguish 0 (node), 1 (edge),
        2 (face), and 3 (volume) dimensional elements. A mesh's connectivity
        array is dependent on the type of connectivity:
            - 1D : edge_node_connectivity required (nEdges, 2)
            - 2D : face_node_connectivity required (nFaces, 3); 
                   edge_node_connectivity optional
            - 3D : volume_node_connectivity required (nVolumes, MaxNumNodesPerVolume);
                   edge_node_connectivity, face_node_connectivity optional
        """

        level = BaseCheck.HIGH
        score = 0
        out_of = 0
        messages = []

        desc = 'Interconnectivity: connection between elements in the mesh'

        if not self.meshes[mesh]['topology_dimension']:
            m = 'Mesh does not contain the required attribute "topology_dimension",'+\
                ' therefore any defined connectivity cannot be verified'
            messages.append(m)
            out_of += 1
            return self.make_result(level, score, out_of, desc, messages)

        # verify that at least the requirements are met
        conns = ['edge_node_connectivity', 'face_node_connectivity', 'volume_node_connectivity']
        dims = [1, 2, 3]

        for _dim, _conn in zip(dims, conns):
            if (not self.meshes[mesh][_conn]) and (self.meshes[mesh]['topology_dimension'] == _dim):
                out_of += 1  # increment out_of, do not increment score
                m = 'dataset is {}D, so must have "{}"'.format(_dim, _conn)
                return self.make_result(level, score, out_of, desc, messages)

        # now we test individual connectivities -- here we will be incrementing the score
        for _conn in conns:
            if self.meshes[mesh][_conn]:
                # validate the expected attributes match
                out_of += 1
                valid, order = self._validate_nc_shape(mesh, _conn)

                # if the order is nonstd, then edge_dim or face_dim is
                # required per the standard and we want to check it exists
                if order == 'nonstd': 
                    self.__check_nonstd_order_dims__(mesh, _conn)

                if valid:
                    score += 1
                else: # notify user of invalid array
                    m = 'Dataset contains invalid "{}" array'.format(_conn)
                    messages.append(m)

                # check for optional attributes edge[face][volume]_coordinates
                self.__check_edge_face_coords__(mesh, _conn)

        return self.make_result(level, score, out_of, desc, messages)


    def _check3_ncoords_exist(self, mesh):
        """
        Checks node coordinates in a given mesh variable. Dependent on
        _check1_topology_dim, _check2_connectivity_attrs.

        :param netCDF4 variable mesh: the mesh variable

        Notes
        -----
        The node coordinates attribute points to the auxiliary coordinate
        variables that represent the locations of the nodes (e.g. latitude,
        longitude, other spatial coordinates). A mesh must have node coordinates
        the same length as the value for mesh's topology dimension.
        Additionally, all node coordinates specified in a mesh must be defined
        as variables in the dataset.
        """

        level = BaseCheck.HIGH
        score = 0
        out_of = 0
        messages = []
        desc = 'Node coordinates point to aux coordinate variables representing' +\
               ' locations of nodes'

        self.meshes[mesh]['node_coordinates'] = []
        if not self.meshes[mesh].get('topology_dimension'):
            msg = 'Failed because no topology dimension exists'
            messages.append(msg)
            out_of += 1
            return self.make_result(level, score, out_of, desc, messages)
        else:
            try:
                ncoords = mesh.node_coordinates.split(' ')
                assert len(ncoords) == self.meshes[mesh].get('topology_dimension')
                for nc in ncoords:
                    try:
                        out_of += 1
                        assert nc in self.ds.variables
                        self.meshes[mesh]['node_coordinates'].append(nc)
                        score += 1
                    except AssertionError:
                        msg = 'Node coordinate "{}" in mesh but not in variables'.format(nc)
                        messages.append(msg)
            except AttributeError:
                msg = 'This mesh has no node coordinate variables'
                out_of += 1
                messages.append(msg)
            except AssertionError:
                msg = 'The size of mesh\'s node coordinates does not match' +\
                      ' the topology dimension ({})'.format(self.meshes[mesh].get('topology_dimension'))
                out_of += 1
                messages.append(msg)

        return self.make_result(level, score, out_of, desc, messages)


    def _check4_edge_face_conn(self, mesh):
        """edge_face_connectivity is a variable pointing to an index of all faces
        that share the same edge -- i.e., are neighbors on an edge. This index
        is thus an array of (nEdges x 2). Zero-based indexing is default.

        Dependent on edge_node_connectivity and  face_node_connectivity (and
        therefore _check2_connectivity_attrs) to have previously defined nEdges
        and the existence of faces.

        :param netCDF4 variable mesh: mesh variable"""

        # TODO: check for start_index, _FillValue?
        level = BaseCheck.LOW
        score = 0
        out_of = 0
        messages = []
        desc = 'array of faces sharing the same edge (optional)'

        if (not self.meshes[mesh]['nedges']) or (not self.meshes[mesh]['nfaces']):
            return self.make_result(level, score, out_of, desc, messages)

        else:
            try:
                efc = mesh.getncattr('edge_face_connectivity')
                out_of += 1
            except AttributeError:
                messages.append('No edge_face_connectivity (optional)')
                return self.make_result(level, score, out_of, desc, messages)
            # check if efc has the right shape
            try:
                dim1, dim2 = self.ds.variables[efc].shape        # unpack the tuple
                assert dim1 == self.meshes[mesh]['nedges'].size  # compare to nedges
                assert dim2 == 2                                 # should be equal to 2
                score += 1
            except AssertionError:
                messages.append('Incorrect shape ({}, {}) of edge_face_connectivity array'.format(dim1, dim2))
                
        return self.make_result(level, score, out_of, desc, messages)


    def _check5_face_edge_conn(self, mesh):
        """face_edge_connectivity is a variable pointing to an index of each
        edge of each face; it's an array of shape (nFaces x MaxNumNodesPerFace). 
        Zero-based indexing is default.If a face has fewer corners/edges
        than MaxNumNodesPerFace, the last edge indices should be equal to
        _FillValue, and the indexing should start at start_index.

        Dependent on face_node_connectivity--and thus 
        _check2_connectivity_attrs--to have previously defined the
        existence of faces. Skipped if maxnumnodesperface is not defined.

        :param netCDF4 variable mesh: mesh variable"""

        level = BaseCheck.LOW
        score = 0
        out_of = 0
        messages = []
        desc = 'array pointing to every index of each edge of each face (optional)'

        valid, _out_of, msg = self.__check_fec_ffc__(mesh, 'face_edge_connectivity')
        out_of += _out_of
        messages.append(msg)

        if valid:
           score += 1
                
        return self.make_result(level, score, out_of, desc, messages)


    def _check6_face_face_conn(self, mesh):
        """
        face_face_connectivity is a variable pointing to an index identifying
        every face that shares an edge with another face. The array should be
        (nFaces x MaxNumNodesPerFace). Zero-based indexing default. 

        Dependent on face_node_connectivity to have previously defined nFaces.

        :param netCDF4 variable mesh: mesh variable"""

        level = BaseCheck.LOW
        score = 0
        out_of = 0
        messages = []
        desc = 'array of every face sharing a face with any other face (optional)'

        valid, _out_of, msg = self.__check_fec_ffc__(mesh, 'face_face_connectivity')
        out_of += _out_of
        messages.append(msg)

        if valid:
           score += 1
                
        return self.make_result(level, score, out_of, desc, messages)



    def check_run(self, _):
        """
        Loop through meshes of the dataset and perform the UGRID standard
        checks on them. Each mesh is a dict of {mesh: {attr: val, ...}}

        Parameters
        ----------
        _ : placeholder
            The compliance checker runs each method beginning with 'check_' by
            calling the higher-level method `_run_check(c, ds)`, where c is the
            check method and ds is the given dataset. Since the UgridChecker
            runs the `setup()` method and assigns the dataset to self.ds, the
            ds passed with `_run_check(c, ds)` doesn't actually need to be used,
            but still needs a place to go so this method doesn't break; it is
            'absorbed' by this placeholder.

        Returns
        -------
        ret_vals : list
            Results of the check methods that have been run
        """

        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'Run UGRID checks if mesh variables are present in the data'
        ret_vals = []
        if self.meshes:
            score += 1
            for mesh in self.meshes:
                for name, check in self.yield_checks():
                    r = check(mesh)
                    ret_vals.append(check(mesh))
        else:
            msg = 'No mesh variables are detected in the data; all checks fail.'
            messages.append(msg)
        ret_vals.append(self.make_result(level, score, out_of, desc, messages))
        return ret_vals


    def yield_checks(self):
        """Iterate checks"""
        for name in sorted(dir(self)):
            if name.startswith('_check'):
                yield name, getattr(self, name)


    def __check_edge_face_coords__(self, mesh, cty):
        """
        Check the edge[face] coordinates of a given mesh.

        Notes
        -----
        Edge[face] coordinates are optional, and point to the auxiliary coordinate
        variables associated with the 'characteristic location' (e.g. midpoint)
        of the edge. These coorindates have length nEdges, and may have a
        `bounds` attribute specifying the bounding coords of the edge (which
        duplicates the information in the node_coordinates variables).


        edge_coordinates requires edge_node_connectivity, which is required if
        the mesh is 1D and optional if it is 2D or 3D.

        :param netCDF4 variable mesh: mesh variable
        :param str cty              : node connectivity type; one of
                                      edge_node_connectivity or
                                      face_node_connctivity
        """

        # TODO implement fully 3D volume checks

        level = BaseCheck.LOW
        score = 0
        out_of = 1
        messages = []
        desc = 'Edge coordinates point to aux coordinate variables representing' +\
               ' locations of edges (usually midpoint)'

        coordmap = {
            'edge_node_connectivity': 'edge_coordinates',
            'face_node_connectivity': 'face_coordinates',
        } 

        varmap = {
            'edge_coordinates': 'nedges',
            'face_coordinates': 'nfaces',
        }

        # do(es) the mesh(es) have appropriate connectivity? If not, pass
        if (not self.meshes[mesh][cty]):
            messages.append('No {}?'.format(cty))
            return self.make_result(level, score, out_of, desc, messages)

        # first ensure the _coordinates variable exists
        _c = coordmap[cty]
        try:
            coords = mesh.getncattr(_c)
        except AttributeError:
            messages.append('Optional attribute, not required')
            return self.make_result(level, score, out_of, desc, messages)

        # if it exists, verify its length is equivalent to nedges
        try:
            for coord in coords.split(' '): # split the string
                _coord_len = len(self.ds.variables[coord])
                _dim_len = len(self.ds.dimensions[varmap[_c]])
                assert _coord_len == _dim_len
            score += 1
        except AssertionError:
            m = '{} should have length of {}'.format(_c, varmap[_c])
            messages.append(m)

        return self.make_result(level, score, out_of, desc, messages)


    def __check_fec_ffc__(self, mesh, cty):
        """Checks for the optional variable/attribute of face_edge_connectivity
        or face_face_connectivity and verifies the shape

        :param netCDF4 variable mesh: mesh variable
        :param str cty              : connectivity type; one of face_edge or
                                      face_face_connectivity

        :returns bool, int, str"""

        # TODO: check for start_index, _FillValue?

        valid = False
        _out_of = 0
        m = ''

        try:
            mnpf = self.ds.dimensions.get('maxnumnodesperface')
        except AttributeError: # skip
            return valid, _out_of, ''

        if (not self.meshes[mesh]['nfaces']):
            m += 'Number of faces (nfaces) not defined'
            return valid, _out_of, m

        else:

            try:
                _c = mesh.getncattr(cty)
                _out_of += 1
            except AttributeError:
                m += 'No {} (optional)'.format(cty)
                return valid, _out_of, m

            # check if right shape
            try:
                dim1, dim2 = self.ds.variables[_c].shape         # unpack the tuple
                assert dim1 == self.meshes[mesh]['nfaces'].size  # compare to nfaces
                assert dim2 == mnpf.size                         # should be equal
                valid = True
            except AssertionError:
                m += 'Incorrect shape ({}, {}) of {} array'.format(dim1, dim2, cty)
 
            return valid, _out_of, m
        
    
    def __check_nonstd_order_dims__(self, mesh, cty):
        """If a connectivity variable pointed to by edge_node_connectivity,
        face_node_connectivity has dimensions listed in non-standard order,
        the appropriate dimension variable must also exist. Respectively
        edge_dimension and face_dimension.

        :param netCDF4 variable mesh: mesh variable being checked
        :param str cty              : node connectivity type"""

        level = BaseCheck.MEDIUM
        score = 0
        out_of = 1
        messages = []

        dim_map = {  # map to correct dimension requirement
            'edge_node_connectivity': 'edge_dimension',
            'face_node_connectivity': 'face_dimension'
        }

        desc = '{} required when dimension orderomg of '.format(dim_map[cty]) +\
               ' {} vars is non-standard order'.format(cty)

        # check for the approrpiate dimension
        exists, msg = self.__check_edge_face_dim__(mesh, dim_map[cty])

        # if exists (True), increment score
        if exists:
            score += 1
        else:
            messages.append(msg)

        return self.make_result(level, score, out_of, desc, messages)


    def __check_edge_face_dim__(self, mesh, dim_var):
        """
        Check the existence of edge_dimension of a given mesh

        :param netCDF4 variable mesh: the mesh variable
        :param str dim_var          : dimension variable to check for

        Notes
        -----
        An edge/face dimension is only required when dimension ordering of any of the
        edge connectivity variables (edge_node_connectivity,
        face_edge_connectivity) is non-standard. An example of this would be
        edge_node_connectivity = (2, nEdges) (standard ordering) vs (nEdges, 2),
        the non-standard ordering, where nEdges is the number of edges found in
        a dataset. nEdges is the edge dimension.

        # TODO: Find an example of non-standard face_edge_connectivity
        """

        try:
            # assign the value of *_dimension, as described above
            self.meshes[mesh][dim_var] = self.ds.dimensions[mesh.getncattr(dim_var)]
            return True, None
        except AttributeError:
            msg = 'Mesh does not contain {}, '.format(dim_var)+\
                  'required when connectivity in non-standard order.'
            return False, msg
        except KeyError:
            msg = 'Edge dimension defined in mesh, not defined in dataset ' +\
                  'dimensions'
            return False, msg


    def _validate_nc_shape(self, mesh, cty):
        """For each mesh, ensure the array that the edge/face/node_connectivity
        variable points to has shape of
            (nEdges, 2) or (2, nEdges) if irregularly ordered # edge_node
            (nFaces, 3) or (3, nFaces) # face_node_conn
            (nVolumes, MaxNumNodesPerVolume) or (MaxNumNodesPerVolume, nVolumes)
        This assumes that the dataset has dimensions defined for the number of
        edges, faces, volumes, and max number of nodes per volume.


        :param netCDF4 object mesh: mesh variable
        :param str cty            : connectivity type; one of
                                    edge_node_connectivity,
                                    face_node_connectivity,
                                    volume_node_connectivity

        :returns bool: indicator if valid shape and if 'regular' ordering"""

        try:
            assert cty in ['edge_node_connectivity', 'face_node_connectivity', 'volume_node_connectivity']
            conn_array_name = mesh.getncattr(cty)
        except AssertionError:
            return False, None # should never get this, right?
        except AttributeError:
            return False, None

        # use name of array to get that variable from the dataset
        _array = self.ds.variables.get(conn_array_name)
        _d1name, _d2name = _array.dimensions # tuple of strings
        dim1 = self.ds.dimensions[_d1name]   # access the dimension objects
        dim2 = self.ds.dimensions[_d2name]
 
        # check against dimensions of dataset
        try:
            assert dim1.name in self.ds.dimensions.keys()
            assert dim2.name in self.ds.dimensions.keys()
        except AssertionError:
            return False, None

        # determine ordering
        # NOTE how I check dim2.size; if dim2 does happen to be the "3" variable, 
        # it could be called literally whatever the modeler wants. What's important is
        # the size. This could be said for the n(Edges)Faces dimension, but this is not
        # assumed as some sort of standard must be applied

        if cty == 'edge_node_connectivity':
            _dim1 = 'nedges'
            _dim2size = 2
        elif cty == 'face_node_connectivity':
            _dim1 = 'nfaces'
            _dim2size = 3
        else:
            raise NotImplementedError # haven't dealt with real 3D grids yet

        if (dim1.name == _dim1) and (dim2.size == _dim2size):
            # set the attr in the meshes dict
            self.meshes[mesh][_dim1] = self.ds.dimensions[_dim1]
            return True, 'regular'
        elif (dim1.size == _dim2size) and (dim2.name == _dim1):
            self.meshes[mesh][_dim1] = self.ds.dimensions[_dim1]
            return True, 'nonstd'
        else:
            return False, None


