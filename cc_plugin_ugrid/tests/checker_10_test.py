#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import logging
import unittest
import tempfile
from pkg_resources import resource_filename as rs

import netCDF4 as nc4

from cc_plugin_ugrid.checker_10 import UgridChecker10
from cc_plugin_ugrid import logger
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class TestUgridChecker10(unittest.TestCase):
    """Testing class for UGRID checks"""

    def nc(self, ncpath):
        """
        Return an opened netCDF4 dataset.

        Parameters
        ----------
        ncpath : str
            path to .nc file
        """
        _, tf = tempfile.mkstemp(suffix='.nc')
        shutil.copy(ncpath, tf)
        ncd = nc4.Dataset(tf, 'r+')
        self.addCleanup(ncd.close)
        self.addCleanup(lambda: os.remove(tf))
        return ncd

    def setUp(self):
        """Method to run before every test"""
        dspath = os.path.join(os.getcwd(), 'cc_plugin_ugrid', 'resources', 'ugrid.nc')
        dataset = self.nc(dspath)
        self.checker = UgridChecker10()
        self.checker.setup(dataset)

    def test_expected_pass(self):
        """
        The Ugridchecker10 is set up to loop through the mesh variables inside a
        dataset, and then loop through the tests for each of these meshes. We
        leverage this structure to construct the tests for checks that are
        expected to pass.
        """
        r = self.checker.check1_topology_exists()
        assert r.value[0] == r.value[1]

        for mt in self.checker.meshes:

            r = self.checker._check2_topology_dim(mt)
            assert r.value[0] == r.value[1]

            r = self.checker._check3_connectivity(mt)
            assert r.value[0] == r.value[1]

            r = self.checker._check4_ncoords_exist(mt)
            assert r.value[0] == r.value[1]

            r = self.checker._check8_edge_dimension(mt)
            assert r.value[0] == r.value[1]

    def test_fail_check1_topology_exists(self):
        """Test that check1_topology_exists fails without a topology variable"""
        self.checker.meshes = {}
        r = self.checker.check1_topology_exists()
        assert r.value[0] != r.value[1]

    def test_fail_check2_topology_dim(self):
        """Test _check2_topology_dim fails when the topology dimension is not in
        [1, 2, 3]"""
        for mesh in self.checker.meshes:
            mesh.topology_dimension = 999
            r = self.checker._check2_topology_dim(mesh)
            assert r.value[0] != r.value[1]

    def test_fail_check3_connectivity(self):
        """Test _check3_connecivity fails when the defined connectivity vars are
        not in the variables."""
        for mesh in self.checker.meshes:
            self.checker._check2_topology_dim(mesh)
            # run check that passes to get the appropriate connectivity_type
            self.checker._check3_connectivity(mesh)
            # get the connectivity inside the dataset, alter
            conn_type = self.checker.meshes[mesh].get('connectivity')
            setattr(mesh, conn_type, 'THIS IS A DRILL')
            # rerun to failure
            r = self.checker._check3_connectivity(mesh)
            assert r.value[0] != r.value[1]

    def test_fail_check4_ncoords_exist(self):
        """Test the absence of node coordinates in a dataset."""
        for mesh in self.checker.meshes:
            self.checker._check2_topology_dim(mesh)
            del mesh.node_coordinates
            r = self.checker._check4_ncoords_exist(mesh)
            assert r.value[0] != r.value[1]
