"""Ugrid Checker."""

import logging

from compliance_checker.base import BaseNCCheck, Result

try:
    from ._version import __version__
except ImportError:
    __version__ = "unknown"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class UgridExceptionError(Exception):  # noqa: D101
    pass


class UgridChecker(BaseNCCheck):
    """Ugrid Checker."""

    _cc_spec = "UGRID"
    _cc_url = "https://github.com/ioos/cc-plugin-ugrid"
    _cc_author = "Brian McKenna <brian.mckenna@rpsgroup.com>"
    _cc_checker_version = __version__

    @classmethod
    def beliefs(cls):
        """Beliefs."""
        return {}

    @classmethod
    def make_result(cls, level, score, out_of, name, messages):
        """Make result."""
        return Result(level, (score, out_of), name, messages)

    def setup(self, ds):
        """UGRID checker.

        Assign the dataset and create the dict of meshes it will need to check through.

        Check for attribute existence in the mesh. If an attribute exists,
        each check will assign the value of the attribute to the mesh
        dictionary. Otherwise, the attribute in the mesh dict is set as None.

        **No validation of the attribute is performed.**

        Args:
            ds : netCDF4 dataset object

        """
        self.ds = ds
        self.meshes = {
            m: {}
            for m in self.ds.get_variables_by_attributes(
                cf_role="mesh_topology",
            )
        }

        for mesh in self.meshes:
            for att in (
                "boundary_node_coordinates",
                "edge_coordinates",
                "edge_dimension",
                "edge_face_connectivity",
                "edge_node_connectivity",
                "face_coordinates",
                "face_dimension",
                "face_edge_coordinates",
                "face_face_connectivity",
                "face_node_connectivity",
                "nedges",
                "nfaces",
                "node_coordinates",
                "topology_dimension",
                "volume_dimension",
                "volume_edge_coordinates",
                "volume_face_connectivity",
                "volume_node_connectivity",
                "volume_coordinates",
                "volume_shape_type",
                "volume_volume_connectivity",
            ):
                if hasattr(mesh, att):
                    self.meshes[mesh][att] = mesh.getncattr(att)
                else:
                    self.meshes[mesh][att] = None
