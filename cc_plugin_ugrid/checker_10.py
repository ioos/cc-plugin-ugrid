import re
from cc_plugin_ugrid import UgridChecker, logger
from compliance_checker.base import BaseCheck

# we'll want to take this out for production
import netCDF4 as nc4

class UgridChecker10(UgridChecker):

    _cc_spec_version = '1.0'
    _cc_description = 'UGRID {} compliance-checker'.format(_cc_spec_version)
    _cc_display_headers = {
        3: 'Highly Recommended',
        2: 'Recommended',
        1: 'Suggested'
    }

    METHODS_REGEX = re.compile('(\w+: *\w+) \((\w+: *\w+)\) *')
    PADDING_TYPES = [ "none", "low", "high", "both" ]

    def __init__(self):
        """Initialize a UgridCheker10 for a given dataset."""
        pass

    def check1_topology_exists(self):
        """
        Check the dataset has at least one mesh topology. Fails if not.
        This is the only check in the UgridCheker10 class defined without
        '_check' in the name; it only needs to run once, whereas the other
        checks run through a generator to check against each mesh.

        Notes
        -----
        The topology dimension indicates the highest dimensionality of the
        elements in the data.
        """
        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'mesh_topology variable exists'

        if len(self.meshes) >= 1:
            score += 1
        else:
            msg = 'No mesh variable are contained in the dataset.'
            messages.append(msg)
        # TODO NOTE LOOK maybe this result could be the condition to prompt the
        # loop through the meshes and complete the rest of the checks
        return self.make_result(level, score, out_of, desc, messages)

    def _check2_topology_dim(self, mesh):
        """
        Check the dimension of the mesh topology. The result of this check is a
        dependency for the following checks:
            - check_connectivity
            - check_node_coords

        Parameters
        ----------
        mesh : netCDF4 mesh variable
        """
        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'The topology dimension is the highest dimension of the data'
        # if self.check1_topology_exists():
        if len(self.meshes) > 0:
            try:
                assert mesh.topology_dimension in [1, 2, 3]
                self.meshes[mesh]['topo_dim'] = mesh.topology_dimension
                score += 1
            except AssertionError:
                self.meshes[mesh]['topo_dim'] = None
                msg = 'Mesh topology dimension not 1, 2, or 3D.'
                messages.append(msg)
            except AttributeError:
                self.meshes[mesh]['topo_dim'] = None
                msg = 'No topology dimension exists in this mesh'
                messages.append(msg)
        else:
            msg = 'Failed because check1_topology_exists failed.'
            messages.append(msg)
        return self.make_result(level, score, out_of, desc, messages)

    def _check3_connectivity(self, mesh):
        """
        Check the connecivity of a given mesh. Dependent on
        check1 and _check2_topology_dim.

        Dependecy for:
            - check_face_dimension
                - check_face_coords
                - check_loc_in_vars
            - check_edge_dimension

        Parameters
        ----------
        mesh : netCDF4 mesh variable

        Notes
        -----
        A mesh's (inter)connectivity is the inter-connection of geometrical
        elements in the mesh. A mesh can distinguish 0 (node), 1 (edge),
        2 (face), and 3 (volume) dimensional elements. A mesh's connectivity
        array is dependent on the type of connectivity:
            - 1D : matrix of dimension (nEdges, 2)
            - 2D : matrix of dimension (nFaces, 3)
            - 3D : matrix of dimension (nVolumes, MaxNumNodesPerVolume)
        """
        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'Interconnectivity: connection between elements in the mesh'
        self.meshes[mesh]['connectivity'] = None
        self.meshes[mesh]['connectivity_array'] = None
        if not self.meshes[mesh].get('topo_dim'):
            return self.make_result(level, score, out_of, desc, messages)
        else:
            try:
                if self.meshes[mesh].get('topo_dim') == 1:
                    conn_type = 'edge_node_connectivity'
                elif self.meshes[mesh].get('topo_dim') == 2:
                    conn_type = 'face_node_connectivity'
                elif self.meshes[mesh].get('topo_dim') == 3:
                    conn_type = 'volume_node_connectivity'
                else:
                    conn_type = 'FAIL' # should never happen
                conn_vars = mesh.getncattr(conn_type)
                assert conn_vars in self.ds.variables
                self.meshes[mesh]['connectivity'] = conn_type
                self.meshes[mesh]['connectivity_array'] = self.ds.variables[conn_vars]
                score += 1
            except AttributeError:
                msg = '"{}" attribute does not exist in mesh'.format(conn_type)
                messages.append(msg)
            except AssertionError:
                msg = '"{}" value "{}" is not a variable'.format(
                    conn_type, conn_vars
                )
                messages.append(msg)

        return self.make_result(level, score, out_of, desc, messages)

    def _check4_ncoords_exist(self, mesh):
        """
        Checks node coordinates in a given mesh variable. Dependent on
        check1_topology_exists, _check2_topology_dim.

        Parameters
        ----------
        mesh : netCDF4 mesh variable

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
        out_of = 1
        messages = []
        desc = 'Node coordinates point to aux coordinate variables representing' +\
               ' locations of nodes'
        self.meshes[mesh]['node_coordinates'] = []
        if not self.meshes[mesh].get('topo_dim'):
            msg = 'Failed because no topology dimension exists'
            messages.append(msg)
            return self.make_result(level, score, out_of, desc, messages)
        else:
            try:
                ncoords = mesh.node_coordinates.split(' ')
                assert len(ncoords) == self.meshes[mesh].get('topo_dim')
                for nc in ncoords:
                    try:
                        assert nc in self.ds.variables
                        self.meshes[mesh]['node_coordinates'].append(nc)
                    except AssertionError:
                        msg = 'Node coordinate "{}" in mesh but not in variables'.format(nc)
                        messages.append(msg)
                score += 1
            except AttributeError:
                msg = 'This mesh has no node coordinate variables'
                messages.append(msg)
            except AssertionError:
                msg = 'The size of mesh\'s node coordinates does not match' +\
                      ' the topology dimension ({})'.format(self.topo_dim)
                messages.append(msg)

            return self.make_result(level, score, out_of, desc, messages)

    def _check5_edge_coordinates(self, mesh):
        """
        Check the edge coordinates of a given mesh.

        Notes
        -----
        Edge coordinates are optional, and points to the auxiliary coordinate
        variables associated with the 'characteristic location' (e.g. midpoint)
        of the edge. These coorindates have lemgth nEdges, and may have a
        `bounds` attribute specifying the bounding coords of the edge (which
        duplicates the information in the node_coordinates variables).
        """
        # TODO
        pass

    def _check6_face_coordinates(self, mesh):
        """
        Check the face coordinates of a given mesh.

        Notes
        -----
        Face coordinates are an optional variable and point to the auxiliary
        coordinate variables associated with the characteristic location of the
        faces.
        """
        # TODO
        pass

    def _check7_volume_coordinates(self, mesh):
        """Check the volume coordinates of a given mesh"""
        # TODO
        pass

    def _check8_edge_dimension(self, mesh):
        """
        Check the edge dimension of a given mesh. Dependent on
        check_connectivity.

        Parameters
        ----------
        mesh : netCDF4 dataset variable

        Notes
        -----
        An edge dimension is only required when dimension ordering of any of the
        edge connectivity variables (edge_node_connectivity,
        face_edge_connectivity) is non-standard. An example of this would be
        edge_node_connectivity = (2, nEdges) vs (nEdges, 2), where nEdges is the
        number of edges found in a dataset. nEdges is the edge dimension.

        # TODO: Find an example of non-standard face_edge_connectivity
        """
        level = BaseCheck.MEDIUM
        score = 0
        out_of = 1
        messages = []
        desc = 'Edge dimension required when ordering of dimension of edge ' +\
               'connectivity vars is non-standard'
        if not self.meshes[mesh].get('connectivity'):
            msg = 'Failed because mesh contains no specified connectivity'
            messages.append(msg)
            return self.make_result(level, score, out_of, desc, messages)
        else:
            try:
                # assign nEdges the value of edge_dimension, as described above
                self.meshes[mesh]['nEdges'] = self.ds.dimensions[mesh.edge_dimension]
                # NOTE this currently assumes that if the edge_dimension var
                # is defined, one or more of the edge connectivity variables is
                # defined in non-standard order.
                score += 1
                msg = 'Edge dimension defined; assuming one more more edge ' +\
                      'connectivity vars dimensions are non-standard order'
            except AttributeError:
                msg = 'Mesh does not contain optional edge_dimension variable;'+\
                      ' assuming that edge connectivity variables are defined '+\
                      'in standard order.'
                messages.append(msg)
                score += 1  # because it's optional
            except KeyError:
                msg = 'Edge dimension defined in mesh not defined in data ' +\
                      'dimensions'
                messages.append(msg)
        return self.make_result(level, score, out_of, desc, messages)

    def _check9_check_face_dimension(self, mesh):
        """Check the face dimension of a given mesh"""
        # TODO
        pass

    def _check_10_volume_dimension(self, mesh):
        """Check volume dimension of a given mesh"""
        # TODO
        pass

    def _check_11_volume_shape_type(self, mesh):
        """
        Check the volume shape type of a given mesh. Required for 3D meshes.
        Dependent on _check2_topology_dim and _check3_connecivity.

        Parameters
        ----------
        mesh : netCDF4 dataset variable

        Notes
        -----
        For each volume in the mesh, this variable specifies its shape by
        pointing to a flag variable: tetrahedron, pyramid, wedge, or hexahedron.
        This flag variable must have the same dimension as number of volumes
        contained in the mesh.
        """
        level = BaseCheck.HIGH
        score = 0
        out_of = 1
        messages = []
        desc = 'Required variable defining the shape of each volume'
        if self.meshes[mesh].get('topo_dim') == 3 and\
           self.meshes[mesh].get('connectivity_array'):
            vol_types = None
            try:
                assert mesh.volume_shape_type in self.ds.variables
                vol_types = mesh.volume_shape_type
            except KeyError:
                msg = 'Mesh does not contain required volume_shape_type variable'
            except AssertionError:
                msg = 'volume_shape_type variable "{}" not defined in dataset'+\
                      ' variables'
            if vol_types:
                nVols = self.meshes[mesh].get('connectivity_array').shape[0]
                assert vol_types.shape == nVols
                score += 1
            return self.make_result(level, score, out_of, desc, messages)
        else:
            pass

    def yield_checks(self):
        """Iterate checks"""
        for name in sorted(dir(self)):
            if name.startswith('_check'):
                yield name, getattr(self, name)

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
