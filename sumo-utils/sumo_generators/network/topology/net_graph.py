from collections import defaultdict

from sumo_generators.network.topology.net_topology import NetTopology, retrieve_edge_information
from sumo_generators.static.constants import *


class NetGraph(NetTopology):
    """
    Class representing the network graph

    :param valid_edges: valid topology edges
    :type valid_edges: list
    :param num_rows: number of matrix rows
    :type num_rows: int
    :param num_cols: number of matrix cols
    :type num_cols: int
    """

    def __init__(self, traci, valid_edges: list, num_rows: int = MIN_ROWS, num_cols: int = MIN_COLS):
        # Store the valid edges
        super().__init__(traci, valid_edges, num_rows, num_cols)

        self._network = defaultdict(list)

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
        self._network[source].append({'to': destination,
                                      'out_edge': {f'{source}_{destination}':
                                                       self.retrieve_turn_edges(f'{source}_{destination}',
                                                                                is_single_cross_grid)},
                                      'in_edge': {f'{destination}_{source}':
                                                      self.retrieve_turn_edges(f'{destination}_{source}',
                                                                               is_single_cross_grid)}
                                      })

    def get_adjacent_nodes_by_source(self, source_node: str):
        """
        Get adjacent nodes given a node

        :param source_node: source junction node
        :type source_node: str
        :return: adjacent nodes identifiers
        :rtype: list
        """
        return [node['to'] for node in self._network.get(source_node)]

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

        # Iterate over the network graph nodes
        for node, value in self._network.items():
            # Iterate over each possible node destination
            for possible_destination in value:
                # Retrieve turn edges (right, left and forward) of outer edges
                for edge, out_edges in possible_destination['out_edge'].items():
                    edge_turns.update(retrieve_edge_information(edge, out_edges, cols))
                # Retrieve turn edges (right, left and forward) of inner edges
                for edge, in_edges in possible_destination['in_edge'].items():
                    edge_turns.update(retrieve_edge_information(edge, in_edges, cols))

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
        destination_info = None
        # Iterate over the possible destinations of the current junction
        for possible_destination in self._network.get(source):
            # Retrieve the information if its available
            if possible_destination['to'] == destination:
                destination_info = possible_destination['out_edge']
                break
        return destination_info
