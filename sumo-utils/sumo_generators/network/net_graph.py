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
        # In order to generate valid 1x1 grid
        is_single_cross_grid = False
        if self._net_matrix.shape[0] == 3 and self._net_matrix.shape[1] == 3:
            is_single_cross_grid = True

        # Iterate over the matrix
        for i in range(0, self._net_matrix.shape[0]):
            for j in range(0, self._net_matrix.shape[1]):
                # Get the source node
                source = self._net_matrix[i, j]
                # Exclude non-valid values and avoid unwanted values and non-existent connections
                if source != '0':
                    # NORTH: Only connect lower node
                    if 'n' in source:
                        destination = self._net_matrix[i + 1, j]
                        if destination != '0':
                            self.add_edges(source, destination, is_single_cross_grid)
                    # SOUTH: Only connect upper node
                    if 's' in source:
                        destination = self._net_matrix[i - 1, j]
                        if destination != '0':
                            self.add_edges(source, destination, is_single_cross_grid)
                    # WEST: Only connect right node
                    if 'w' in source:
                        destination = self._net_matrix[i, j + 1]
                        if destination != '0':
                            self.add_edges(source, destination, is_single_cross_grid)
                    # EAST: Only connect left node
                    if 'e' in source:
                        destination = self._net_matrix[i, j - 1]
                        if destination != '0':
                            self.add_edges(source, destination, is_single_cross_grid)
                    if 'c' in source:
                        # No need to check if destination is '0' due to representation
                        # Lower node
                        self.add_edges(source, self._net_matrix[i + 1, j], is_single_cross_grid)
                        # Upper node
                        self.add_edges(source, self._net_matrix[i - 1, j], is_single_cross_grid)
                        # Right node
                        self.add_edges(source, self._net_matrix[i, j + 1], is_single_cross_grid)
                        # Left node
                        self.add_edges(source, self._net_matrix[i, j - 1], is_single_cross_grid)

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
        self._graph[source].append({'to': destination,
                                    'out_edge': {f'{source}_{destination}':
                                                     self.retrieve_turn_edges(f'{source}_{destination}',
                                                                              is_single_cross_grid)},
                                    'in_edge': {f'{destination}_{source}':
                                                    self.retrieve_turn_edges(f'{destination}_{source}',
                                                                             is_single_cross_grid)}
                                    })

    def retrieve_turn_edges(self, edge: str, is_single_cross_grid: bool = False) -> dict:
        """
        Retrieve the edges related to performing right, left and forward turns.

        :param edge: edge name
        :type edge: str
        :param is_single_cross_grid: flag used for 1x1 grids. Default to False
        :type is_single_cross_grid: bool
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
                turn_edges['left'] = f'c{destination_id}_e1'
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
                    # Calculate south nodes
                    south_destination = ns_outer_edge
                    if ns_outer_edge == 0:
                        south_destination = self._num_cols
                    turn_edges['left'] = f'c{destination_id}_c{upper_edge}'
                    turn_edges['right'] = f'c{destination_id}_s{south_destination}'
                else:
                    turn_edges['left'] = f'c{destination_id}_c{upper_edge}'
                    turn_edges['right'] = f'c{destination_id}_c{lower_edge}'

                # Right-side roads
                if ns_outer_edge == 0:
                    turn_edges['forward'] = f'c{destination_id}_e{ew_outer_edge}'
                else:
                    turn_edges['forward'] = f'c{destination_id}_c{right_edge}'
            # From right to left
            elif source_id == right_edge:
                # Up-side roads
                if ew_outer_edge == 1:
                    turn_edges['left'] = f'c{destination_id}_c{lower_edge}'
                    turn_edges['right'] = f'c{destination_id}_n{destination_id}'
                # Down-side roads
                elif ew_outer_edge == self._num_rows:
                    # Calculate south nodes
                    south_destination = ns_outer_edge
                    if ns_outer_edge == 0:
                        south_destination = self._num_cols
                    turn_edges['left'] = f'c{destination_id}_s{south_destination}'
                    turn_edges['right'] = f'c{destination_id}_c{upper_edge}'
                else:
                    turn_edges['left'] = f'c{destination_id}_c{lower_edge}'
                    turn_edges['right'] = f'c{destination_id}_c{upper_edge}'
                # Left-side roads
                if ns_outer_edge == 1:
                    turn_edges['forward'] = f'c{destination_id}_w{ew_outer_edge}'
                else:
                    turn_edges['forward'] = f'c{destination_id}_c{left_edge}'
            # From down to up
            elif source_id == lower_edge:
                # Right-side roads
                if ns_outer_edge == 0:
                    turn_edges['left'] = f'c{destination_id}_c{left_edge}'
                    turn_edges['right'] = f'c{destination_id}_e{int(destination_id / self._num_rows)}'
                # Left-side roads
                elif ns_outer_edge == 1:
                    turn_edges['left'] = f'c{destination_id}_w{ew_outer_edge}'
                    turn_edges['right'] = f'c{destination_id}_c{right_edge}'
                else:
                    turn_edges['left'] = f'c{destination_id}_c{left_edge}'
                    turn_edges['right'] = f'c{destination_id}_c{right_edge}'
                # Up-side roads
                if ew_outer_edge == 1:
                    turn_edges['forward'] = f'c{destination_id}_n{destination_id}'
                else:
                    turn_edges['forward'] = f'c{destination_id}_c{upper_edge}'
            # From up to down
            elif source_id == upper_edge:
                # Right-side roads
                if ns_outer_edge == 0:
                    turn_edges['left'] = f'c{destination_id}_e{int(destination_id / self._num_rows)}'
                    turn_edges['right'] = f'c{destination_id}_c{left_edge}'
                # Left-side roads
                elif ns_outer_edge == 1:
                    turn_edges['left'] = f'c{destination_id}_c{right_edge}'
                    turn_edges['right'] = f'c{destination_id}_w{ew_outer_edge}'
                else:
                    turn_edges['left'] = f'c{destination_id}_c{right_edge}'
                    turn_edges['right'] = f'c{destination_id}_c{left_edge}'

                # Down-side roads
                if ew_outer_edge == self._num_rows:
                    # Calculate south nodes
                    south_destination = ns_outer_edge
                    if ns_outer_edge == 0:
                        south_destination = self._num_cols
                    turn_edges['forward'] = f'c{destination_id}_s{south_destination}'
                else:
                    turn_edges['forward'] = f'c{destination_id}_c{lower_edge}'

        # Replace invalid values with '' or if its 1x1 grid with the valid value
        for turn, edge in turn_edges.items():
            if edge not in self._valid_edges:
                if edge != '' and is_single_cross_grid:
                    # Update 1x1 grid values, retrieve actual edge
                    new_edges = [item for item in GRID_1x1_DICT[edge] if item[0] == source and turn == item[1]]
                    # Set new value
                    turn_edges[new_edges[0][1]] = new_edges[0][2]
                else:
                    turn_edges[turn] = ''

        return turn_edges

    def get_adjacent_nodes_by_node(self, source_node: str):
        """
        Get adjacent nodes given a node

        :param source_node: source junction node
        :type source_node: str
        :return: adjacent nodes identifiers
        :rtype: list
        """
        return [node['to'] for node in self._graph.get(source_node)]

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
