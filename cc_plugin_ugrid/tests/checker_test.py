import logging
import os
import shutil
import tempfile
import unittest

import netCDF4 as nc4

from cc_plugin_ugrid import logger
from cc_plugin_ugrid.checker import UgridChecker

logger.addHandler(logging.NullHandler())
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class TestUgridChecker(unittest.TestCase):
    """Testing class for UGRID checks"""

    def nc(self, ncpath):
        """
        Return an opened netCDF4 dataset.

        :param str ncpath : path to .nc file
        """

        _, tf = tempfile.mkstemp(suffix=".nc")
        shutil.copy(ncpath, tf)
        ncd = nc4.Dataset(tf, "r+")
        self.addCleanup(ncd.close)
        self.addCleanup(lambda: os.remove(tf))
        return ncd

    def setUp(self):
        """Method to run before every test"""

        dspath = os.path.join(os.getcwd(), "cc_plugin_ugrid", "resources", "ugrid.nc")
        dataset = self.nc(dspath)
        self.checker = UgridChecker()
        self.checker.setup(dataset)  # initializes dict of meshes

    def test_expected_pass(self):
        """
        The UgridChecker is set up to loop through the mesh variables inside a
        dataset, and then loop through the tests for each of these meshes. We
        leverage this structure to construct the tests for checks that are
        expected to pass.
        """

        for mt in self.checker.meshes:
            r = self.checker._check1_topology_dim(mt)
            assert r.value[0] == r.value[1]

            r = self.checker._check2_connectivity_attrs(mt)
            assert r.value[0] == r.value[1]

            r = self.checker._check3_ncoords_exist(mt)
            assert r.value[0] == r.value[1]

            r = self.checker._check4_edge_face_conn(mt)
            assert r.value[0] == r.value[1]

            r = self.checker._check5_face_edge_conn(mt)
            assert r.value[0] == r.value[1]

            r = self.checker._check6_face_face_conn(mt)
            assert r.value[0] == r.value[1]

    # testing for correct failure behavior
    def test_fail_check1_topology_dim(self):
        """Test that _check1_topology_dim fails without the wrong variable
        and without a topology variable"""

        # set wrong value for topo dimension for each mesh
        for mt in self.checker.meshes:
            self.checker.meshes[mt]["topology_dimension"] = "NotMyProblem"
            r = self.checker._check1_topology_dim(mt)
            assert r.value[0] != r.value[1]

        # set no meshes at all
        self.checker.meshes = {}
        for mt in self.checker.meshes:
            r = self.checker._check1_topology_dim(mt)
            assert r.value[0] != r.value[1]

    def test_fail_check2_connectivity_attrs(self):
        """Test _check2_connectivity_attrs fails when the given topology dimensions
        do not match"""

        for mesh in self.checker.meshes:
            # remove the attrs
            self.checker.meshes[mesh]["edge_node_connectivity"] = None
            self.checker.meshes[mesh]["face_node_connectivity"] = None
            r = self.checker._check2_connectivity_attrs(mesh)
            assert r.value[0] != r.value[1]

        # fresh dataset
        self.setUp()

        # change the array the connectivity points to something else
        for mesh in self.checker.meshes:
            mesh.setncattr("edge_node_connectivity", "fec")
            mesh.setncattr("face_node_connectivity", "fec")
            r = self.checker._check2_connectivity_attrs(mesh)
            assert r.value[0] != r.value[1]

    def test_fail_check_edge_face_coords(self):
        """Called by the _check2_connectivity_attrs is a check to see if the
        optional attributes edge_coordinates, face_coordinates, and
        volume_coordinates exist. This test seeks to fail this check."""

        for mesh in self.checker.meshes:
            # change the face_coordinates variable; this essentially
            #   changes the lengths of the vars
            mesh.setncattr("face_coordinates", "lon lat")
            r = self.checker.__check_edge_face_coords__(mesh, "face_node_connectivity")
            assert r.value[0] != r.value[1]

    def test_fail_check_nonstd_order_dims(self):
        """
        Embedded within the _check2_connectivity_attrs is a test to verify
        the existence of edge_dimension or face_dimension, but only if the
        edge[face]_node_connectivity array is found to be in non-standard order."""

        for mesh in self.checker.meshes:
            # remove edge_dimension
            mesh.delncattr("edge_dimension")
            r = self.checker.__check_nonstd_order_dims__(mesh, "edge_node_connectivity")
            assert r.value[0] != r.value[1]

        self.setUp()  # fresh dataset

        for mesh in self.checker.meshes:
            # remove face_dimension
            mesh.delncattr("face_dimension")
            r = self.checker.__check_nonstd_order_dims__(mesh, "face_node_connectivity")
            assert r.value[0] != r.value[1]

    def test_fail_check3_ncoords_exist(self):
        """Test _check3_ncoords_exist fails appropriately."""

        # remove topology dimension
        for mesh in self.checker.meshes:
            self.checker.meshes[mesh]["topology_dimension"] = None
            r = self.checker._check3_ncoords_exist(mesh)
            assert r.value[0] != r.value[1]

        # fresh dataset
        self.setUp()

        # remove node coordinates
        for mesh in self.checker.meshes:
            del mesh.node_coordinates
            r = self.checker._check3_ncoords_exist(mesh)
            assert r.value[0] != r.value[1]

        self.setUp()

        # change the array length (2 to 3)
        for mesh in self.checker.meshes:
            mesh.setncattr("node_coordinates", "['lat', 'lon', 'both']")
            r = self.checker._check3_ncoords_exist(mesh)
            assert r.value[0] != r.value[1]

        # change the vars themselves
        for mesh in self.checker.meshes:
            mesh.setncattr("node_coordinates", "['notacoord', 'nope']")
            r = self.checker._check3_ncoords_exist(mesh)
            assert r.value[0] != r.value[1]

    def test_fail_check4_edge_face_conn(self):
        """Fail the edge_face_connectivity check"""

        for mesh in self.checker.meshes:
            # change the edge_face_connectivity array
            mesh.setncattr("edge_face_connectivity", "nv")
            self.checker._check2_connectivity_attrs(mesh)  # run the dependency
            r = self.checker._check4_edge_face_conn(mesh)
            assert r.value[0] != r.value[1]

    def test_fail_check5_face_edge_conn(self):
        """Fail the face_edge_connectivity check"""

        for mesh in self.checker.meshes:
            # change the face_edge_connectivity array
            mesh.setncattr("face_edge_connectivity", "nv")
            self.checker._check2_connectivity_attrs(mesh)  # run the dependency
            r = self.checker._check5_face_edge_conn(mesh)
            assert r.value[0] != r.value[1]

    def test_fail_check6_face_face_conn(self):
        """Fail the face_face_connectivity check"""

        for mesh in self.checker.meshes:
            # change the face_face_connectivity array
            mesh.setncattr("face_face_connectivity", "nv")
            self.checker._check2_connectivity_attrs(mesh)  # run the dependency
            r = self.checker._check6_face_face_conn(mesh)
            assert r.value[0] != r.value[1]
