import math
import random
from abc import ABC, abstractmethod

from sumo_generators.network.node_matrix import NodeMatrix
from sumo_generators.static.constants import *


def retrieve_edge_information(edge: str, turns: dict, cols: int) -> dict:
    """
    Retrieve turns edge information

    :param edge: source edge name
    :type edge: str
    :param turns: turns edges of the source edge
    :type turns: str
    :param cols: number of columns of the network topology
    :type cols: int
    :return: dictionary with the edge and turns information
    :rtype: dict
    """
    edge_info = {}
    # Check if there is information available
    if turns['right'] and turns['left'] and turns['forward']:
        # Retrieve source and destination nodes and its ids
        source, destination = edge.split('_')
        source_id, destination_id = int(source[1:]), int(destination[1:])

        # Calculate direction
        direction = ''
        if 'n' in source or 's' in source:
            direction = 'ns'
        elif 'e' in source or 'w' in source:
            direction = 'ew'
        else:  # center nodes
            if source_id == destination_id - cols or source_id == destination_id + cols:  # Going down/up
                direction = 'ns'
            elif source_id == destination_id + 1 or source_id == destination_id - 1:  # Going right/left
                direction = 'ew'

        # Calculate opposite direction
        opposite_direction = 'ns' if direction == 'ew' else 'ew'

        # Insert the edges information with probabilities of 0.0 and its direction
        # It is split, to retrieve the junction name
        edge_info[edge] = {'right': {'junction': turns['right'].split('_')[1], 'prob': 0.0,
                                     'direction': opposite_direction},
                           'left': {'junction': turns['left'].split('_')[1], 'prob': 0.0,
                                    'direction': opposite_direction},
                           'forward': {'junction': turns['forward'].split('_')[1], 'prob': 0.0,
                                       'direction': direction}}

    else:  # Otherwise leave empty
        edge_info[edge] = {'right': {'junction': '', 'prob': 0.0, 'direction': ''},
                           'left': {'junction': '', 'prob': 0.0, 'direction': ''},
                           'forward': {'junction': '', 'prob': 0.0, 'direction': ''}}

    return edge_info


class NetTopology(ABC):
    """
    Class representing the network (abstract)

    """

    def __init__(self, traci, valid_edges: list, num_rows: int = MIN_ROWS, num_cols: int = MIN_COLS):
        # Store traci instance
        self._traci = traci
        # Store the valid edges
        self._valid_edges = valid_edges
        # Define the number of rows and columns of the topology
        self._num_rows = num_rows
        self._num_cols = num_cols

        # Define the network matrix in order to generate the graph
        # Plus two due to the outer edges
        node_matrix = NodeMatrix(num_rows=num_rows + 2, num_cols=num_cols + 2)
        self._node_matrix = node_matrix.generate_connections_matrix()

        self._network = None

    def generate_network(self) -> None:
        """
        Generates a network representation with its information and connections

        :return: None
        """
        # In order to generate valid 1x1 grid
        is_single_cross_grid = False
        if self._node_matrix.shape[0] == 3 and self._node_matrix.shape[1] == 3:
            is_single_cross_grid = True

        # Iterate over the matrix
        for i in range(0, self._node_matrix.shape[0]):
            for j in range(0, self._node_matrix.shape[1]):
                # Get the source node
                source = self._node_matrix[i, j]
                # Exclude non-valid values and avoid unwanted values and non-existent connections
                if source != '0':
                    # NORTH: Only connect lower node
                    if 'n' in source:
                        destination = self._node_matrix[i + 1, j]
                        if destination != '0':
                            self.add_edges(source, destination, is_single_cross_grid)
                    # SOUTH: Only connect upper node
                    if 's' in source:
                        destination = self._node_matrix[i - 1, j]
                        if destination != '0':
                            self.add_edges(source, destination, is_single_cross_grid)
                    # WEST: Only connect right node
                    if 'w' in source:
                        destination = self._node_matrix[i, j + 1]
                        if destination != '0':
                            self.add_edges(source, destination, is_single_cross_grid)
                    # EAST: Only connect left node
                    if 'e' in source:
                        destination = self._node_matrix[i, j - 1]
                        if destination != '0':
                            self.add_edges(source, destination, is_single_cross_grid)
                    if 'c' in source:
                        # No need to check if destination is '0' due to representation
                        # Lower node
                        self.add_edges(source, self._node_matrix[i + 1, j], is_single_cross_grid)
                        # Upper node
                        self.add_edges(source, self._node_matrix[i - 1, j], is_single_cross_grid)
                        # Right node
                        self.add_edges(source, self._node_matrix[i, j + 1], is_single_cross_grid)
                        # Left node
                        self.add_edges(source, self._node_matrix[i, j - 1], is_single_cross_grid)

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

    def update_route_with_turns(self, traffic_lights: dict, turn_prob_by_edges: dict) -> None:
        """
        Update the vehicles routes based on the turn probabilities and count them

        :param traffic_lights: dictionary with the traffic lights of the simulation
        :type traffic_lights: dict
        :param turn_prob_by_edges: dictionary with the probabilities of turning per edge
        :type turn_prob_by_edges: dict
        :return: None
        """
        # Get all vehicles from simulation
        vehicles = self._traci.vehicle.getIDList()

        # Iterate over the vehicles
        for vehicle in vehicles:
            # Get current vehicle road, origin and destination
            vehicle_road = self._traci.vehicle.getRoadID(vehicle)
            # Exclude inner edges
            if ':' not in vehicle_road:
                # Retrieve origin and destination junctions
                source, destination = vehicle_road.split('_')

                # Retrieve destination info
                destination_info = self.retrieve_destination_info(source, destination)

                # Retrieve next traffic light
                next_junction = destination if 'c' in destination else ''

                # Target edge and turn
                target_edge, turn = '', ''
                # Check if there is next traffic light, if the vehicle is not counted and the next junction info is
                # available
                if next_junction != '' and not \
                        traffic_lights[next_junction].is_vehicle_turning_counted(vehicle_id=vehicle) and \
                        destination_info:
                    # Retrieve turn type [0.0, 1.0)
                    turn_type = random.random()

                    # Retrieve turn probabilities for each direction
                    turn_right, turn_left, turn_forward = list(turn_prob_by_edges[vehicle_road].values())

                    if turn_type < turn_forward:  # forward
                        turn = 'forward'
                    elif turn_type < turn_right:  # right
                        turn = 'right'
                    elif turn_type < turn_left:  # left
                        turn = 'left'

                    # Calculate the new target edge
                    target_edge = destination_info[f'{source}_{destination}'][turn]

                    # Calculate if the target edge is valid
                    if target_edge != '':
                        # Retrieve vehicle type to find new route
                        cur_vehicle_type = self._traci.vehicle.getTypeID(vehicle)
                        # Find new route
                        new_route = self._traci.simulation.findRoute(fromEdge=vehicle_road, toEdge=target_edge,
                                                                     vType=cur_vehicle_type).edges

                        # Check if there are routes available (from and to) based on the current vehicle type
                        if new_route:
                            # Set new route
                            self._traci.vehicle.setRoute(vehicle, new_route)

                            # Increase the TL turn counter
                            traffic_lights[next_junction].increase_turning_vehicles(turn)

                            # Add new vehicle
                            traffic_lights[next_junction].append_turning_vehicle(vehicle_id=vehicle)

    def calculate_turning_vehicles(self, traffic_lights: dict) -> None:
        """
        Calculate the turning vehicles based on its route

        :param traffic_lights: dictionary with the traffic lights of the simulation
        :type traffic_lights: dict
        :return: None
        """

        # Get all vehicles from simulation
        vehicles = self._traci.vehicle.getIDList()

        # Iterate over the vehicles
        for vehicle in vehicles:
            # Get next junction
            next_junction = self._traci.vehicle.getNextTLS(vehicle)
            # Get current vehicle road, origin and destination
            vehicle_road = self._traci.vehicle.getRoadID(vehicle)
            # Exclude inner edges and check if it has edges
            if ':' not in vehicle_road and next_junction:
                # Get closest junction
                next_junction = next_junction[0][0]
                # Check if vehicle is not counted
                if next_junction and not traffic_lights[next_junction].is_vehicle_turning_counted(vehicle_id=vehicle):
                    # Retrieve vehicle route and current edge
                    veh_route = self._traci.vehicle.getRoute(vehicle)
                    cur_edge_index = self._traci.vehicle.getRouteIndex(vehicle)
                    # It is not at the end of the simulation
                    if cur_edge_index != len(veh_route):
                        # Get the current edge and junction
                        current_edge = veh_route[cur_edge_index]
                        current_junction = current_edge.split('_')[0]
                        # Retrieve next edge
                        next_edge = veh_route[cur_edge_index + 1]

                        possible_turns = self.retrieve_destination_info(current_junction, next_junction)

                        # Initialize turn direction
                        turn = ''
                        # Iterate over the possible turns in order to find the actual turn
                        for edge, turns in possible_turns.items():
                            for k, v in turns.items():
                                # If the next edge is on the possible turns, retrieve the turn
                                if v == next_edge:
                                    turn = k

                        # Increase the number of turning vehicles on the given direction
                        if turn:
                            traffic_lights[next_junction].increase_turning_vehicles(turn)

                    # Count new vehicle
                    traffic_lights[next_junction].append_turning_vehicle(vehicle_id=vehicle)

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def get_adjacent_nodes_by_source(self, source_node: str) -> dict:
        """
        Get adjacent nodes given a node

        :param source_node: source junction node
        :type source_node: str
        :return: adjacent nodes identifiers
        :rtype: dict
        """
        raise NotImplementedError

    @abstractmethod
    def retrieve_turns_edges(self, cols: int) -> dict:
        """
        Retrieve the turn edges for all the edges of the network topology

        :param cols: number of columns of the topology
        :type cols: int
        :return: turn edges for all the edges
        :rtype: dict
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @property
    def network(self) -> dict:
        """
        Getter of the network graph

        :return: network graph
        :rtype: numpy ndarray
        """
        return self._network

    @network.setter
    def network(self, network) -> None:
        """
        Setter of the network graph

        :param network: network graph
        :return: None
        """
        self._network = network
