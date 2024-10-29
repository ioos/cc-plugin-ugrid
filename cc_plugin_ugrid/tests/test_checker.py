"""Testing class for UGRID checks."""

import logging
from pathlib import Path

import pytest
from netCDF4 import Dataset

from cc_plugin_ugrid import logger
from cc_plugin_ugrid.checker import UgridChecker

logger.addHandler(logging.NullHandler())
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

ugridnc = Path(__file__).absolute().parent.parent.joinpath("resources", "ugrid.nc")


@pytest.fixture
def checker():
    """Load checker."""
    dset = Dataset(
        ugridnc,
        "r+",
        diskless=True,
        persist=False,
    )
    uchecker = UgridChecker()
    uchecker.setup(dset)

    yield uchecker
    dset.close()


def test_expected_pass(checker):
    """The UgridChecker is set up to loop through the mesh variables inside a
    dataset, and then loop through the tests for each of these meshes. We
    leverage this structure to construct the tests for checks that are
    expected to pass.
    """
    for mt in checker.meshes:
        r = checker._check1_topology_dim(mt)
        assert r.value[0] == r.value[1]

        r = checker._check2_connectivity_attrs(mt)
        assert r.value[0] == r.value[1]

        r = checker._check3_ncoords_exist(mt)
        assert r.value[0] == r.value[1]

        r = checker._check4_edge_face_conn(mt)
        assert r.value[0] == r.value[1]

        r = checker._check5_face_edge_conn(mt)
        assert r.value[0] == r.value[1]

        r = checker._check6_face_face_conn(mt)
        assert r.value[0] == r.value[1]


# testing for correct failure behavior
def test_fail_check1_topology_dim(checker):
    """Test that _check1_topology_dim fails without the wrong variable and without a topology variable."""
    # set wrong value for topo dimension for each mesh
    for mt in checker.meshes:
        checker.meshes[mt]["topology_dimension"] = "NotMyProblem"
        r = checker._check1_topology_dim(mt)
        assert r.value[0] != r.value[1]

    # set no meshes at all
    checker.meshes = {}
    for mt in checker.meshes:
        r = checker._check1_topology_dim(mt)
        assert r.value[0] != r.value[1]


def test_fail_check2_connectivity_attrs(checker):
    """Test _check2_connectivity_attrs fails when the given topology dimensions do not match."""
    for mesh in checker.meshes:
        # remove the attrs
        checker.meshes[mesh]["edge_node_connectivity"] = None
        checker.meshes[mesh]["face_node_connectivity"] = None
        r = checker._check2_connectivity_attrs(mesh)
        assert r.value[0] != r.value[1]


def test_fail_check2_connectivity_attrs_bad_point(checker):
    """Change the array the connectivity points to something else."""
    for mesh in checker.meshes:
        mesh.setncattr("edge_node_connectivity", "fec")
        mesh.setncattr("face_node_connectivity", "fec")
        r = checker._check2_connectivity_attrs(mesh)
        assert r.value[0] != r.value[1]


def test_fail_check_edge_face_coords(checker):
    """Called by the _check2_connectivity_attrs is a check to see if the
    optional attributes edge_coordinates, face_coordinates, and
    volume_coordinates exist. This test seeks to fail this check.
    """
    for mesh in checker.meshes:
        # change the face_coordinates variable; this essentially
        #   changes the lengths of the vars
        mesh.setncattr("face_coordinates", "lon lat")
        r = checker.__check_edge_face_coords__(
            mesh,
            "face_node_connectivity",
        )
        assert r.value[0] != r.value[1]


def test_fail_check_nonstd_order_dims(checker):
    """Embedded within the _check2_connectivity_attrs is a test to verify
    the existence of edge_dimension or face_dimension, but only if the
    edge[face]_node_connectivity array is found to be in non-standard order.
    """
    for mesh in checker.meshes:
        # remove edge_dimension
        mesh.delncattr("edge_dimension")
        r = checker.__check_nonstd_order_dims__(
            mesh,
            "edge_node_connectivity",
        )
        assert r.value[0] != r.value[1]


def test_fail_check_nonstd_order_dims_no_face_dim(checker):
    """Remove face_dimension."""
    for mesh in checker.meshes:
        mesh.delncattr("face_dimension")
        r = checker.__check_nonstd_order_dims__(
            mesh,
            "face_node_connectivity",
        )
        assert r.value[0] != r.value[1]


def test_fail_check3_ncoords_exist(checker):
    """Test _check3_ncoords_exist fails appropriately."""
    # remove topology dimension
    for mesh in checker.meshes:
        checker.meshes[mesh]["topology_dimension"] = None
        r = checker._check3_ncoords_exist(mesh)
        assert r.value[0] != r.value[1]


def test_fail_check3_ncoords_exist_no_node_coords(checker):
    """Remove node coordinates."""
    for mesh in checker.meshes:
        del mesh.node_coordinates
        r = checker._check3_ncoords_exist(mesh)
        assert r.value[0] != r.value[1]


def test_fail_check3_ncoords_exist_diff_arr_len(checker):
    """Change the array length (2 to 3)."""
    for mesh in checker.meshes:
        mesh.setncattr("node_coordinates", "['lat', 'lon', 'both']")
        r = checker._check3_ncoords_exist(mesh)
        assert r.value[0] != r.value[1]

    # change the vars themselves
    for mesh in checker.meshes:
        mesh.setncattr("node_coordinates", "['notacoord', 'nope']")
        r = checker._check3_ncoords_exist(mesh)
        assert r.value[0] != r.value[1]


def test_fail_check4_edge_face_conn(checker):
    """Fail the edge_face_connectivity check."""
    for mesh in checker.meshes:
        # change the edge_face_connectivity array
        mesh.setncattr("edge_face_connectivity", "nv")
        checker._check2_connectivity_attrs(mesh)  # run the dependency
        r = checker._check4_edge_face_conn(mesh)
        assert r.value[0] != r.value[1]


def test_fail_check5_face_edge_conn(checker):
    """Fail the face_edge_connectivity check."""
    for mesh in checker.meshes:
        # change the face_edge_connectivity array
        mesh.setncattr("face_edge_connectivity", "nv")
        checker._check2_connectivity_attrs(mesh)  # run the dependency
        r = checker._check5_face_edge_conn(mesh)
        assert r.value[0] != r.value[1]


def test_fail_check6_face_face_conn(checker):
    """Fail the face_face_connectivity check."""
    for mesh in checker.meshes:
        # change the face_face_connectivity array
        mesh.setncattr("face_face_connectivity", "nv")
        checker._check2_connectivity_attrs(mesh)  # run the dependency
        r = checker._check6_face_face_conn(mesh)
        assert r.value[0] != r.value[1]
