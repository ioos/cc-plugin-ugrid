import re
from cc_plugin_ugrid import UgridChecker, logger
from compliance_checker.base import BaseCheck

# NOTE take this out for production?
import netCDF4 as nc4

class UgridChecker20(UgridChecker):

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
        """Initialize UgridChecker20 for a given dataset. Set all mesh
        attributes that we are about to check to None.
        
        Check for attribute existence in the mesh. If an attribute exists,
         each check will assign the value of the attribute to the mesh
        dictionary. No validation of the attribute is performed."""

        for mesh in self.meshes.keys():
            for att in ['boundary_node_coordinates', 'edge_coordinates',
                'edge_dimension', 'edge_face_connectivity', 'edge_node_connectivity', 
                'face_coordinates', 'face_dimension', 'face_edge_coordinates',
                'face_face_connectivity', 'face_node_connectivity', 'node_coordinates',
                'topology_dimension', 'volume_dimension', 'volume_edge_coordinates',
                'volume_face_connectivity', 'volume_node_connectivity',
                'volume_coordinates', 'volume_shape_type', 'volume_volume_connectivity'
                ]:
                if mesh.getncattr(att):
                    self.meshes[mesh][att] = mesh.getncattr(att)
                else:
                    self.meshes[mesh][att] = None


    def _check_topology_dim(self, mesh):
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
            score += 1
        except AssertionError:
            m = 'Invalid topology_dimension "{}" of type "{}"'.format(
                self.meshes[mesh]['topology_dimension'],
                type(self.meshes[mesh]['topology_dimension']))
            messages.append(m)

        return self.make_result(level, score, out_of, desc, messages)


    def _check_connectivity_attrs(self, mesh):
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
            - 2D : face_node_connecivity required (nFaces, 3); 
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
            m = 'Mesh does not contain the required attribute "topology_dimension"'\+
                ' therefore any defined connectivity cannot be verified'
            messages.append(m)
            out_of += 1
            return self.make_result(level, score, out_of, desc, messages)

        # verify that at least the requirements are met
        conns = ['edge_node_connectivity', 'face_node_connectivity', 'volume_node_connectivity']
        dims = [1, 2, 3]
        for _dim, _conn in zip(dims, conns):
            if (not self.meshes[mesh][_conn]) and (self.meshes[mesh]['topology_dimension'] == _dim):
                out_of += 1
                m = 'dataset is {}D, so must have "{}"'.format(_dim, _conn)
                return self.make_result(level, score, out_of, desc, messages)

        # now we test individual connectivities
        for _conn in conns:
            if self.meshes[mesh][_conn]:
                # TODO
                pass


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
