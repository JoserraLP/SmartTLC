import numpy as np
from sumo_generators.network.topology.net_topology import NetTopology, retrieve_edge_information
from sumo_generators.static.constants import *


class NetMatrix(NetTopology):
    """
    Class representing the network graph as a matrix

    :param traci: TraCI simulation
    :param valid_edges: valid topology edges
    :type valid_edges: list
    :param num_rows: number of matrix rows
    :type num_rows: int
    :param num_cols: number of matrix cols
    :type num_cols: int
    """

    def __init__(self, traci, valid_edges: list, num_rows: int = MIN_ROWS, num_cols: int = MIN_COLS):
        # Store the TraCI instance
        super().__init__(traci, valid_edges, num_rows, num_cols)

        # Get a list of the junction names
        self._nodes_names = [self._node_matrix[i][j] for i in range(num_rows + 2) for j in range(num_cols + 2)
                             if self._node_matrix[i][j] != '0']
        self._nodes_names.sort()

        # Create the matrix
        self._network = np.full((len(self._nodes_names), len(self._nodes_names)), {})
        np.diag(self._network, 0)

    def add_edges(self, source: str, destination: str, is_single_cross_grid: bool = False) -> None:
        """
        Add the edge information to the graph base on two nodes.
        Schema is 'to' node along with 'out_edge' and 'in_edge' with the turn edges.

        :param source: source node identifier
        :type source: str
        :param destination: destination node identifier
        :type destination: str
        :param is_single_cross_grid: flag used for 1x1 grids. Default to False
        :type is_single_cross_grid: bool
        :return: None
        """
        source_index, destination_index = int(self._nodes_names.index(source)), int(
            self._nodes_names.index(destination))

        # Retrieve info from one of the lanes of the edge as the info is the for all of them
        road_info = {'from': source,
                     'to': destination,
                     'distance': self._traci.lane.getLength(f'{source}_{destination}_0'),
                     'edge': f'{source}_{destination}',
                     'turns': self.retrieve_turn_edges(f'{source}_{destination}', is_single_cross_grid)
                     }

        # Store the info in the matrix
        self._network[source_index][destination_index] = road_info

    def get_adjacent_nodes_by_source(self, source_node: str):
        """
        Get adjacent nodes given a node

        :param source_node: source junction node
        :type source_node: str
        :return: adjacent nodes identifiers
        :rtype: list
        """
        # Get source node index
        source_node_index = self._nodes_names.index(source_node)

        # Retrieve the name of those adjacent nodes
        adjacent_nodes_names = [self._network[source_node_index][i]['to']
                                for i in range(len(self._network[source_node_index]))
                                if self._network[source_node_index][i]]

        return adjacent_nodes_names

    def retrieve_turns_edges(self, cols: int) -> dict:
        """
        Retrieve the turn edges for all the edges of the network topology

        :param cols: number of columns of the topology
        :type cols: int
        :return: turn edges for all the edges
        :rtype: dict
        """
        # Initialize edge dictionary
        edge_turns = {}

        # Retrieve upper-triangle indexes without the diagonal
        row_idx, col_idx = np.triu_indices(len(self._nodes_names), k=1)

        # Iterate over the indexes
        for i, j in zip(row_idx, col_idx):
            edge_info = self._network[i][j]
            if edge_info:
                edge_turns.update(retrieve_edge_information(edge=edge_info['edge'],
                                                            turns=edge_info['turns'],
                                                            cols=cols))

        return edge_turns

    def retrieve_destination_info(self, source: str, destination: str) -> dict:
        """
        Retrieve the destination info based on possible directions

        :param source: source node name
        :type source: str
        :param destination: destination node name
        :type destination: str
        :return: destination info
        :rtype: dict
        """
        # Get index from source and destination
        source_idx, destination_idx = self._nodes_names.index(source), self._nodes_names.index(destination)

        # Store the edge id and the turns
        destination_info = {
            self._network[source_idx][destination_idx]['edge']: self._network[source_idx][destination_idx]['turns']
        }

        return destination_info