import math
from collections import defaultdict

from sumo_generators.network.net_matrix import NetMatrix
from sumo_generators.static.constants import *


class NetGraph:
    """
    Class representing the network graph

    :param valid_edges: valid topology edges
    :type valid_edges: list
    :param num_rows: number of matrix rows
    :type num_rows: int
    :param num_cols: number of matrix cols
    :type num_cols: int
    """

    def __init__(self, valid_edges: list, num_rows: int = MIN_ROWS, num_cols: int = MIN_COLS):
        # Store the valid edges
        self._valid_edges = valid_edges
        # Define the number of rows and columns of the topology
        self._num_rows = num_rows
        self._num_cols = num_cols

        # Define the network matrix in order to generate the graph
        # Plus two due to the outer edges
        network_matrix = NetMatrix(num_rows=num_rows + 2, num_cols=num_cols + 2)
        self._net_matrix = network_matrix.generate_connections_matrix()

        self._graph = defaultdict(list)

    def generate_graph(self) -> None:
        """
        Generates a directed graph with the information of the network and its connections

        :return: None
        """
        # Iterate over the matrix
        for i in range(0, self._net_matrix.shape[0]):
            for j in range(0, self._net_matrix.shape[1]):
                # Get the source node
                source = self._net_matrix[i, j]
                # Exclude non-valid values and avoid unwanted values and non-existent connections
                if source != '0':
                    # Left node
                    if j - 1 >= 0 and 'n' not in source and 's' not in source:
                        destination = self._net_matrix[i, j - 1]
                        if destination != '0':
                            self.add_edges(source, destination)
                    # Right node
                    # Avoid unwanted values and non-existent connections
                    if j + 1 <= self._num_cols - 1 and 'n' not in source and 's' not in source:
                        destination = self._net_matrix[i, j + 1]
                        if destination != '0':
                            self.add_edges(source, destination)
                    # Upper node
                    # Avoid unwanted values and non-existent connections
                    if i - 1 >= 0 and 'w' not in source and 'e' not in source:
                        destination = self._net_matrix[i - 1, j]
                        if destination != '0':
                            self.add_edges(source, destination)
                    # Lower node
                    # Avoid unwanted values and non-existent connections
                    if i + 1 <= self._num_rows - 1 and 'w' not in source and 'e' not in source:
                        destination = self._net_matrix[i + 1, j]
                        if destination != '0':
                            self.add_edges(source, destination)

    def add_edges(self, source: str, destination: str) -> None:
        """
        Add the edge information to the graph base on two nodes.
        Schema is 'to' node along with 'out_edge' and 'in_edge' with the turn edges.

        :param source: source node identifier
        :type source: str
        :param destination: destination node identifier
        :type destination: str
        :return: None
        """
        self._graph[source].append({'to': destination,
                                    'out_edge': {f'{source}_{destination}':
                                                     self.retrieve_turn_edges(f'{source}_{destination}')},
                                    'in_edge': {f'{destination}_{source}':
                                                    self.retrieve_turn_edges(f'{destination}_{source}')}
                                    })

    def retrieve_turn_edges(self, edge: str) -> dict:
        """
        Retrieve the edges related to performing right, left and forward turns.

        :param edge: edge name
        :type edge: str
        :return: dict with right, left and forward edges
        :rtype: dict
        """
        # Retrieve source and destination nodes, along with its identifiers
        source, destination = edge.split('_')
        source_id, destination_id = int(source[1:]), int(destination[1:])

        # Initialize turn edges
        turn_edges = {'right': '', 'left': '', 'forward': ''}

        # Retrieve the closest edges ids
        left_edge = destination_id - 1
        right_edge = destination_id + 1
        upper_edge = destination_id - self._num_cols
        lower_edge = destination_id + self._num_cols
        ew_outer_edge = math.ceil(destination_id / self._num_cols)
        ns_outer_edge = destination_id % self._num_cols

        if 'n' in source:
            # Right-side roads
            if ns_outer_edge == 0:
                turn_edges['left'] = 'c1_e1'
                turn_edges['right'] = f'c{destination_id}_c{left_edge}'
            # Left-side roads
            elif ns_outer_edge == 1:
                turn_edges['left'] = f'c{destination_id}_c{right_edge}'
                turn_edges['right'] = 'c1_w1'
            # Center roads
            else:
                turn_edges['left'] = f'c{destination_id}_c{right_edge}'
                turn_edges['right'] = f'c{destination_id}_c{left_edge}'
            turn_edges['forward'] = f'c{destination_id}_c{lower_edge}'
        elif 's' in source:
            # Right-side roads
            if ns_outer_edge == 0:
                turn_edges['left'] = f'c{destination_id}_c{left_edge}'
                turn_edges['right'] = f'c{destination_id}_e{self._num_rows}'
            # Left-side roads
            elif ns_outer_edge == 1:
                turn_edges['right'] = f'c{destination_id}_c{right_edge}'
                turn_edges['left'] = f'c{destination_id}_w{self._num_rows}'
            # Center roads
            else:
                turn_edges['right'] = f'c{destination_id}_c{right_edge}'
                turn_edges['left'] = f'c{destination_id}_c{left_edge}'
            turn_edges['forward'] = f'c{destination_id}_c{upper_edge}'
        elif 'w' in source:
            # Up-side roads
            if ew_outer_edge == 1:
                turn_edges['left'] = f'c{destination_id}_n1'
                turn_edges['right'] = f'c{destination_id}_c{lower_edge}'
            # Down-side roads
            elif ew_outer_edge == self._num_rows:
                turn_edges['right'] = f'c{destination_id}_s1'
                turn_edges['left'] = f'c{destination_id}_c{upper_edge}'
            # Center roads
            else:
                turn_edges['right'] = f'c{destination_id}_c{lower_edge}'
                turn_edges['left'] = f'c{destination_id}_c{upper_edge}'
            turn_edges['forward'] = f'c{destination_id}_c{right_edge}'
        elif 'e' in source:
            # Up-side roads
            if ew_outer_edge == 1:
                turn_edges['left'] = f'c{destination_id}_c{lower_edge}'
                turn_edges['right'] = f'c{destination_id}_n{self._num_cols}'
            # Down-side roads
            elif ew_outer_edge == self._num_rows:
                turn_edges['right'] = f'c{destination_id}_c{upper_edge}'
                turn_edges['left'] = f'c{destination_id}_s{self._num_cols}'
            # Center roads
            else:
                turn_edges['right'] = f'c{destination_id}_c{upper_edge}'
                turn_edges['left'] = f'c{destination_id}_c{lower_edge}'
            turn_edges['forward'] = f'c{destination_id}_c{left_edge}'
        elif 'c' in source and 'c' in destination:
            # From left to right
            if source_id == left_edge:
                # Up-side roads
                if ew_outer_edge == 1:
                    turn_edges['left'] = f'c{destination_id}_n{destination_id}'
                    turn_edges['right'] = f'c{destination_id}_c{lower_edge}'
                # Down-side roads
                elif ew_outer_edge == self._num_rows:
                    turn_edges['left'] = f'c{destination_id}_c{upper_edge}'
                    turn_edges['right'] = f'c{destination_id}_s{ns_outer_edge}'
                else:
                    turn_edges['left'] = f'c{destination_id}_c{upper_edge}'
                    turn_edges['right'] = f'c{destination_id}_c{lower_edge}'
                turn_edges['forward'] = f'c{destination_id}_c{right_edge}'
            # From right to left
            elif source_id == right_edge:
                # Up-side roads
                if ew_outer_edge == 1:
                    turn_edges['left'] = f'c{destination_id}_c{lower_edge}'
                    turn_edges['right'] = f'c{destination_id}_n{destination_id}'
                # Down-side roads
                elif ew_outer_edge == self._num_rows:
                    turn_edges['left'] = f'c{destination_id}_s{destination_id}'
                    turn_edges['right'] = f'c{destination_id}_c{lower_edge}'
                else:
                    turn_edges['left'] = f'c{destination_id}_c{lower_edge}'
                    turn_edges['right'] = f'c{destination_id}_c{upper_edge}'
                turn_edges['forward'] = f'c{destination_id}_c{left_edge}'
            # From down to up
            elif source_id == lower_edge:
                # Right-side roads
                if ns_outer_edge == 0:
                    turn_edges['left'] = f'c{destination_id}_c{left_edge}'
                    turn_edges['right'] = f'c{destination_id}_e{self._num_rows}'
                # Left-side roads
                elif ns_outer_edge == 1:
                    turn_edges['left'] = f'c{destination_id}_w{ew_outer_edge}'
                    turn_edges['right'] = f'c{destination_id}_c{right_edge}'
                else:
                    turn_edges['left'] = f'c{destination_id}_c{left_edge}'
                    turn_edges['right'] = f'c{destination_id}_c{right_edge}'
                turn_edges['forward'] = f'c{destination_id}_c{upper_edge}'
            # From up to down
            elif source_id == upper_edge:
                # Right-side roads
                if ns_outer_edge == 0:
                    turn_edges['left'] = f'c{destination_id}_e1'
                    turn_edges['right'] = f'c{destination_id}_c{left_edge}'
                # Left-side roads
                elif ns_outer_edge == 1:
                    turn_edges['left'] = f'c{destination_id}_c{right_edge}'
                    turn_edges['right'] = f'c{destination_id}_w{ew_outer_edge}'
                else:
                    turn_edges['left'] = f'c{destination_id}_c{right_edge}'
                    turn_edges['right'] = f'c{destination_id}_c{left_edge}'
                turn_edges['forward'] = f'c{destination_id}_c{lower_edge}'

        # Replace invalid values with ''
        for turn, edge in turn_edges.items():
            if edge not in self._valid_edges:
                turn_edges[turn] = ''

        return turn_edges

    @property
    def graph(self) -> dict:
        """
        Getter of the connection graph

        :return: connection graph
        :rtype: numpy ndarray
        """
        return self._graph

    @graph.setter
    def graph(self, graph) -> None:
        """
        Setter of the connection graph

        :param graph: connection graph
        :return: None
        """
        self._graph = graph
