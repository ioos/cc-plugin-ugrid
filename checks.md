### A (very) Brief Summary of UGRID Conventions
These tests are designed with respect to the [UGRID conventions](http://ugrid-conventions.github.io/ugrid-conventions/).

The UGRID conventions contain a variety of names for geometrical attributes, and the checks output results directly referencing these names. For 1D, 2D, or 3D datasets, the checks will iterate through a series of required attributes. A star (&bigstar;) indicates the convention is required, an o-dot (&odot;) represents optional attributes, and a checkmark (&check;) indicates that our code currently checks for the attribute.   

|Required topology attributes	        |   1D                   |   2D                   |   3D                  | Check Implemented |
| :------------------------------:    | :---:                  | :---:                  | :---:                 | :---------:       |
|cf_role	                            |&bigstar;               |&bigstar;               |&bigstar;              | &check;           |
|topology_dimension	                  |1 &bigstar;             |2 &bigstar;             |3 &bigstar;            | &check;           |
|node_coordinates	                    | &bigstar;              |&bigstar;               | &bigstar;             | &check;           |
|edge_node_connectivity               | &bigstar;              | &odot;                 |    &odot;             | &check;           |
|face_node_connectivity               |                        | &bigstar;              |   &odot;              | &check;           |
|volume_node_connectivity             |                        |                        |&bigstar;              | &check;           |
|volume_shape_type                    |                        |                        |&bigstar;              |                   |
|volume_dimension	                    |                        |                        |&odot;                 |                   |
|face_dimension	                      |                        |&odot;                  |       &odot;          |                   |
|edge_dimension	                      |                        |&odot;                  |       &odot;          |                   |
|edge_coordinates                     | &odot;                 | &odot;                 | &odot;                |                   |
|volume_edge_connectivity	            |                        |                        |&odot;                 |                   |
|volume_face_connectivity	            |                        |                        |&odot;                 |                   |
|volume_volume_connectivity	          |                        |                        | &odot;                |                   |
|face_edge_connectivity	              |                        |&odot;                  |     &odot;            |                   |
|face_face_connectivity               |                        |&odot;                  |                       |                   |
|edge_face_connectivity               |                        |&odot;                  |                       |                   |
|boundary_node_connectivity	          |                        |&odot;                  |          &odot;       |                   |
|volume_coordinates	                  |                        |                        |     &odot;            |                   |
|face_coordinates	                    |                        |&odot;                  |        &odot;         |                   ||

---

### UGRID Plugin Checks

| Check | Summary |
| ----- | ------- |
| ```check_mesh_topology_variable``` | Checks to see if a mesh topology variable exists within the dataset |
| ```check_topology_dimension``` | Verifies the *topology_dimension* attribute is either 1, 2, or 3 |
| ```check_node_coordinates_size``` | Checks that the mesh's *node_coordinates* length is the same as the *topology_dimension* |
| ```check_node_coordinates_exist``` | *node_coordinates* values must be variables in the dataset |
| ```check_connectivity``` | Connectivity must exist between nodes in the dataset, whether the connections are node-node (1D), edge-node (2D), or face-node (3D) ||

---

### What's Next for the UGRID Checker?
As the UGRID Checker plugin is a child of IOOS, its development comes from a variety of open-source and commercial efforts. For an outline of features in development or to contribute to the UGRID Checker, check [here](/roadmap.md) for suggestions.
