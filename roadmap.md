### A Roadmap for the UGRID Checker Plugin

The UGRID Checker currently has the following functional checks:

```
check_mesh_topology_variable
check_topology_dimension
check_node_coordinates_size
check_node_coordinates_exist
check_edge_coordinates_exist
check_connectivity
check_face_coordinates
check_edge_dimension
check_face_dimension

```

We present development suggestions separated by priority to show the current direction of feature development.
All of the features shown below are not currently implemented in the ```UGRID Checker```.

| High-Priority             | Mid-Priority                      | Low-Priority                     |
| :---:                     | :---:                             | :---:                            |
| ```volume_shape_type```   |```volume_dimension```             | ```volume_edge_connectivity```   |
|                           |``` face_edge_connectivity```      | ```volume_face_connectivity```   |
|                           |```boundary_node_connectivity```   | ```volume_volume_connectivity``` |
|                           |                                   | ```face_face_connectivity```     |
|                           |                                   | ```edge_face_connectivity```     |
|                           |                                   | ```volume_coordinates```         ||
