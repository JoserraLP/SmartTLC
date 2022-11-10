from sumo_generators.network.node_matrix import NodeMatrix
from sumo_generators.static.constants import *


class NetGenerator:
    """
    Class representing the network generator

    :param rows: number of matrix rows
    :type rows: int
    :param cols: number of matrix cols
    :type cols: int
    :param lanes: number of lanes per edge
    :type lanes: int
    :param distance: distance between nodes
    :type distance: float
    :param junction: junction type
    :type junction: str
    :param tl_type: central nodes traffic light type
    :type tl_type: str
    :param tl_layout: central nodes traffic light layout
    :type tl_layout: str
    :param nodes_path: directory where the nodes file will be created
    :type nodes_path: str
    :param edges_path: directory where the edges file will be created
    :type edges_path: str
    """

    def __init__(self, rows: int = MIN_ROWS, cols: int = MIN_COLS, lanes: int = MIN_LANES, distance: float = DISTANCE,
                 junction: str = JUNCTION_TYPE, tl_type: str = TL_TYPE, tl_layout: str = TL_LAYOUT,
                 nodes_path: str = DEFAULT_NODES_DIR, edges_path: str = DEFAULT_EDGES_DIR) -> None:

        # Define class attributes
        self._distance = distance
        self._nodes_path = nodes_path
        self._edges_path = edges_path
        self._num_lanes = lanes
        self._junction_type = junction
        self._tl_type = tl_type
        self._tl_layout = tl_layout

        # Define network matrix
        net_matrix = NodeMatrix(num_rows=rows, num_cols=cols)

        # Generate connections matrix
        self._net_matrix = net_matrix.generate_connections_matrix()

    def generate_topology(self) -> None:
        """
        Generate the nodes and edges of the topology and store the generated files

        :return: None
        """

        # Define the files schemas
        all_nodes = """<?xml version="1.0" encoding="UTF-8"?>\n<nodes 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation=
        "http://sumo.dlr.de/xsd/nodes_file.xsd">\n"""

        all_edges = """<?xml version="1.0" encoding="UTF-8"?>\n<edges 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation=
        "http://sumo.dlr.de/xsd/edges_file.xsd">\n"""

        # Iterate over the matrix
        for row in range(self._net_matrix.shape[0]):
            for col in range(self._net_matrix.shape[1]):
                # If the matrix cell is valid, generate the node and edges
                if self._net_matrix[row][col] != '0':
                    # Retrieve the node identifier
                    node_id = self._net_matrix[row][col]

                    # NODES
                    all_nodes += self.generate_node(node_id=node_id, row=row, col=col,
                                                    junction_type=self._junction_type, tl_type=self._tl_type,
                                                    tl_layout=self._tl_layout)

                    # EDGES
                    all_edges += self.generate_edges(node_id=node_id, row=row, col=col)

        # End tags
        all_nodes += "</nodes>"

        all_edges += "</edges>"

        # Store information on each file
        with open(self._nodes_path, "w") as nodes:
            print(all_nodes, file=nodes)

        with open(self._edges_path, "w") as edges:
            print(all_edges, file=edges)

    def generate_edges(self, node_id: str, row: int, col: int) -> str:
        """
        Creates a string representing two edges between a node and the closes center node.

        :param node_id: node identifier
        :type node_id: str
        :param row: row where the node is in the matrix
        :type row: int
        :param col: col where the node is in the matrix
        :type col: int
        :return: string representing the edges of one node
        :rtype: str
        """

        # Define the edges string and the closest center node identifier
        edges, closest_center_id = "", ""

        # Retrieve closest center node identifier depending on the node id
        if 'n' in node_id:
            closest_center_id = self._net_matrix[row + 1][col]
        elif 's' in node_id:
            closest_center_id = self._net_matrix[row - 1][col]
        elif 'e' in node_id:
            closest_center_id = self._net_matrix[row][col - 1]
        elif 'w' in node_id:
            closest_center_id = self._net_matrix[row][col + 1]
        elif 'c' in node_id:
            # The center nodes will be different, as they might check close center connections too
            # Right node
            right_closest_id = self._net_matrix[row][col + 1]
            if 'c' in right_closest_id:
                edges += EDGE_SCHEMA.format(id=node_id + "_" + right_closest_id, from_node=node_id,
                                            to_node=right_closest_id, priority=-1, num_lanes=self._num_lanes)
                edges += EDGE_SCHEMA.format(id=right_closest_id + "_" + node_id, from_node=right_closest_id,
                                            to_node=node_id, priority=-1, num_lanes=self._num_lanes)

            # Below node
            below_closest_id = self._net_matrix[row + 1][col]
            if 'c' in below_closest_id:
                edges += EDGE_SCHEMA.format(id=node_id + "_" + below_closest_id, from_node=node_id,
                                            to_node=below_closest_id, priority=-1, num_lanes=self._num_lanes)
                edges += EDGE_SCHEMA.format(id=below_closest_id + "_" + node_id, from_node=below_closest_id,
                                            to_node=node_id, priority=-1, num_lanes=self._num_lanes)

        # If there are close center node, store the from and to nodes and the priority
        if closest_center_id:
            edges += EDGE_SCHEMA.format(id=node_id + "_" + closest_center_id, from_node=node_id,
                                        to_node=closest_center_id, priority=-1, num_lanes=self._num_lanes)
            edges += EDGE_SCHEMA.format(id=closest_center_id + "_" + node_id, from_node=closest_center_id,
                                        to_node=node_id, priority=-1, num_lanes=self._num_lanes)

        return edges

    def generate_node(self, node_id: str, row: int, col: int, junction_type: str, tl_type: str, tl_layout: str) -> str:
        """
        Creates a string representing one node.

        :param node_id: node identifier
        :type node_id: str
        :param row: row where the node is in the matrix
        :type row: int
        :param col: col where the node is in the matrix
        :type col: int
        :param junction_type: central nodes junction type
        :type junction_type: str
        :param tl_type: central nodes traffic light type
        :type tl_type: str
        :param tl_layout: central nodes traffic light layout
        :type tl_layout: str
        :return: string representing one node
        :rtype: str
        """

        # If the node is the central one, define the type as parameter
        if 'c' in node_id:
            node_type = junction_type
        # Otherwise, type will be priority
        else:
            node_type = 'priority'

        # Generate the node item with the coordinates and the type
        node = NODE_SCHEMA.format(id=node_id, x=col * self._distance,
                                  y=(self._net_matrix.shape[0] - row) * self._distance, type=node_type, tl_type=tl_type,
                                  tl_layout=tl_layout)

        return node
