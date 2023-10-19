### A (very) Brief Summary of UGRID Conventions
These tests are designed with respect to the [UGRID conventions](http://ugrid-conventions.github.io/ugrid-conventions/).

The UGRID conventions contain a variety of names for geometrical attributes, and the checks output results directly referencing these names. For 1D, 2D, or 3D datasets, the checks will iterate through a series of required attributes. A star (&bigstar;) indicates the convention is required, an o-dot (&odot;) represents optional attributes, and a checkmark (&check;) indicates that our code currently checks for the attribute.


| Topology Attributes	              |   1D                   |   2D                   |   3D                  | Check Implemented    |
| :------------------------------:    | :---:                  | :---:                  | :---:                 | :---------:          |
|cf_role	                          | &bigstar;              | &bigstar;              | &bigstar;             | &check;              |
|topology_dimension	                  | 1 &bigstar;            | 2 &bigstar;            | 3 &bigstar;           | &check;              |
|node_coordinates	                  | &bigstar;              | &bigstar;              | &bigstar;             | &check;              |
|edge_coordinates                     | &odot;                 | &odot;                 | &odot;                | &check;              |
|face_coordinates	                  |                        | &odot;                 | &odot;                | &check;              |
|edge_node_connectivity               | &bigstar;              | &odot;                 | &odot;                | &check;              |
|face_node_connectivity               |                        | &bigstar;              | &odot;                | &check;              |
|volume_node_connectivity             |                        |                        | &bigstar;             |                      |
|edge_dimension	                      |                        | &odot;                 | &odot;                | &check;              |
|face_dimension	                      |                        | &odot;                 | &odot;                | &check;              |
|volume_dimension	                  |                        |                        | &odot;                |                      |
|volume_shape_type                    |                        |                        | &bigstar;             |                      |
|volume_coordinates	                  |                        |                        | &odot;                |                      |
|edge_face_connectivity               |                        | &odot;                 |                       | &check;              |
|face_edge_connectivity	              |                        | &odot;                 | &odot;                | &check;              |
|face_face_connectivity               |                        | &odot;                 |                       | &check;              |
|volume_edge_connectivity	          |                        |                        | &odot;                |                      |
|volume_face_connectivity	          |                        |                        | &odot;                |                      |
|volume_volume_connectivity	          |                        |                        | &odot;                |                      |
|boundary_node_connectivity	          |                        | &odot;                 | &odot;                |                      |


This document briefly describes the origins of storing unstructured geospatial data in the Network Common Data Form and the efforts to develop consistent guidelines for modelers. After summarizing core attributes of unstructured data, an example of a non-compliant dataset is given to show how the required metadata information can be created.

Unstructured grids (‘u-grid’) are used in a multitude of spatial modeling scenarios where more flexible grids provide better accuracy and resolution of physical systems. The UGRID Conventions were introduced in an attempt to make specifying the topology of unstructured grids consistent while storing them using the Network Common Data Form (NetCDF).

At its most basic form, the Climate and Forecast (CF) Conventions are sufficient when storing unstructured data in a series of points. Many times it is useful (often times necessary) to know information about the topology of the unstructured grid which the data lies on. The UGRID conventions attempt to address this need by providing metadata guidelines for those storing unstructured data.

The core information that should always be included in the metadata, regardless of the dimension of the data, are:
1.	cf_role: the role of the variable in terms of the CF conventions
2.	topology_dimension: highest dimension of the geometric elements
3.	node_coordinates: node coordinates point to the auxiliary coordinate variables representing the locations of the grid’s nodes (i.e. latitude, longitude, and other spatial coordinates)

Another mandatory piece of metadata, interconnectivity between elements, is dependent on the topology dimension. For one-dimensional grids, one must specify the interconnectivity between edges and nodes in the edge_node_connectivity variable. This variable is a connectivity matrix with dimensions (number of edges x 2). For two-dimensional data, the connection between faces and nodes must be specified in the face_node_connectivity variable with dimensions (number of faces x 3).

Three-dimensional gridding is more complex and nuanced than simple 2D gridding. Some 3-D meshes are known as layered meshes, and actually treat the horizontal and vertical components separately. In this sense, the mesh is actually treated as two-dimensional. This necessitates the addition of several variables to a dataset:
1.	A variable detailing the number of mesh layers included in the dataset dimension variables
2.	A variable describing the surface of the mesh, including two UGRID specific attributes:
a.	mesh attribute, pointing to the mesh of the data
b.	location attribute, describing the location of the surface’
c.	Other attributes are in accordance with CF conventions

3.	A variable describing the layers of the mesh; this variable has dimension equal to the number of layers. It includes several UGRID-specific attributes:
a.	mesh attribute, pointing to the mesh of the data
b.	location attribute, describing the location of each layer

4.	A variable describing the depth of the mesh; this variable has dimension equal to the number of nodes. It’s important to note that this depth variable does not describe the depth between one cell and another, but rather typically denotes the depth at a particular node
a.	Attributes are in accordance with CF conventions


Other metadata is optional and sometimes quite useful, but would require a lengthy digression.

---

### UGRID Plugin Checks

| Check                              | Summary                                                        |
| -----                              | -------                                                        |
| `_check1_topology_dim`             | Check the topology dimension of the mesh                       |
| `_check2_connectivity_attrs`       | Check the connectivity attributes of a given mesh              |
| `_check3_ncoords_exist`            | Verify the node coordinates are properly defined               |
| `_check4_edge_face_connectivity`   | Check the optional edge_face_connectivity variable             |
| `_check5_face_edge_connectivity`   | Check the optional face_edge_connectivity variable             |
| `_check6_face_face_connectivity`   | Check the optional face_face_connectivity variable             |

The `_check2_connectivity_attrs` calls a separate method (`__check_edge_face_coords__) to check `edge_coordinates` and `face_cordinates`.

---

### What's Next for the UGRID Checker?
As the UGRID Checker plugin is a child of IOOS, its development comes from a variety of open-source and commercial efforts. We present development suggestions separated by priority to show the current direction of feature development.

| Needed Features              |
| ---------------              |
| `volume_edge_connectivity`   |
| `volume_face_connectivity`   |
| `volume_volume_connectivity` |
| `boundary_node_connectivity` |
