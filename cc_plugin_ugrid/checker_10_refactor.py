import re
from cc_plugin_ugrid import UgridChecker, logger
from compliance_checker.base import BaseCheck

# we'll want to take this out for production
import netCDF4 as nc4

class UgridChecker10(UgridChecker):

    _cc_spec_version = '1.0'
    _cc_description = 'UGRID {} compliance-checker'.format(_cc_spec_version)

    METHODS_REGEX = re.compile('(\w+: *\w+) \((\w+: *\w+)\) *')
    PADDING_TYPES = [ "none", "low", "high", "both" ]


    # NOTE TODO? Potentially move this functionality to UgridChecker.setup()
    def __init__(self, ncdata):
        """
        Initialize a UgridCheker10 for a given dataset.

        Parameters
        ----------
        ncdata : netCDF4 Dataset object
        """
        self.ds = ncdata
        self.meshes = {
            m:{} for m in self.ds.get_variables_by_attributes(
                cf_role='mesh_topology'
            )
        }


    def check1_topology_exists(self):
        """
        Check the dataset has at least one mesh topology. Fails if not.

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
            self.has_mesh = True
        else:
            m = 'No mesh variable are contained in the dataset.'
            self.has_mesh = False
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
        if self.check1_topology_exists():
            try:
                assert mesh.topology_dimension in [1, 2, 3]
                self.meshes[mesh]['topo_dim'] = mesh.topology_dimension
            except AssertionError:
                mesh['topo_dim'] = None
                msg = 'Mesh topology dimension not 1, 2, or 3D.'
                messages.append(msg)
            except AttributeError:
                mesh['topo_dim'] = None
                msg = 'No topology dimension exists in this mesh'
                messages.append(msg)
        else:
            score += 1
            return self.make_result(level, score, out_of, desc, messages)


    def _check3_connectivity(self, mesh):
        """
        Check the connecivity of a given mesh. Dependent on
        check_topology_exists.

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
            except AttributeError:
                msg = '"{}" attribute does not exist in mesh'.format(conn_type)
                messages.append(msg)
            except AssertionError:
                msg = '"{}" value "{}" is not a variable'.format(
                    conn_type, conn_vars
                )
                messages.append(msg)
            self.meshes[mesh]['connectivity'] = conn_type
            self.meshes[mesh]['connectivity_array'] = conn_vars
            score += 1
        return self.make_result(level, score, out_of, desc, messages)


    def _check4_ncoords_exist(self, mesh):
        """
        Checks node coordinates in a given mesh variable. Dependent on
        check_topology_dim.

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
            except AttributeError:
                msg = 'This mesh has no node coordinate variables'
                messages.append(msg)
            except AssertionError:
                msg = 'The size of mesh\'s node coordinates does not match' +\
                      ' the topology dimension ({})'.format(self.topo_dim)
                messages.append(msg)
        for nc in ncoords:
            try:
                assert nc in self.ds.variables
                self.meshes[mesh]['node_coordinates'].append(nc)
            except AssertionError:
                msg = 'Node coordinate "{}" in mesh but not in variables'.format(nc)
                messages.append(msg)
        score += 1
        return self.make_result(level, score, out_of, desc, messages)


    def _check5_edge_dimension(self, mesh):
        """
        Check the edge dimension of a given mesh. Dependent on
        check_connectivity.

        Notes
        -----
        An edge dimension is only required when dimension ordering of any of the
        edge connectivity variables (edge_node_connectivity,
        face_edge_connectivity) is non-standard. An example of this would be
        edge_node_connectivity = (2, nEdges) vs (nEdges, 2), where nEdges is the
        number of edges found in a dataset. nEdges is the edge dimension.

        # TODO: Can you find an example of non-standard face_edge_connectivity?
        """
        level = BaseCheck.MEDIUM  # correct?
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
                # defined in non-standard order. What does this mean for the
                # rest of the tests?
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
                # don't add to score 
        return self.make_result(level, score, out_of, desc, messages)


    def yield_checks(self):
        """Iterate checks"""
        for name in sorted(dir(self)):
            if name.startswith('_check'):
                yield name, getattr(self, name)

    def run_checks(self):
        """
        Loop through meshes of the dataset and perform the UGRID standard
        checks on them. Each mesh is a dict of {mesh: {attr: val, ...}}
        """
        if self.meshes:
            for mesh in self.meshes:
                print('mesh: {}'.format(mesh))
                for name, check in self.yield_checks():
                    print(name)
                    check(mesh)


if __name__ == '__main__':
    ds = nc4.Dataset('/home/dalton/cc-plugin-ugrid/cc_plugin_ugrid/resources/ugrid.nc')
    checker = UgridChecker10(ds)
    checker.run_checks()
