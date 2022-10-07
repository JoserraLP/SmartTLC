# UTILS
import copy
import math
import random

import pandas as pd
from sumo_generators.network.net_graph import NetGraph
from sumo_generators.static.constants import DEFAULT_DATE_MONTH, DEFAULT_DATE_YEAR, DEFAULT_DATE_DAY, DEFAULT_DAY, \
    DATE_FIELDS, TIMESTEPS_PER_HALF_HOUR, DEFAULT_TURN_DICT


def get_topology_dim(traci):
    """
    Retrieve the dimensions of the network topology: rows and cols

    :param traci: TraCI instance
    :return: number of rows and cols
    """
    # Retrieve those valid edges (without ':' character as those are generated by sumo in junctions)
    valid_edges = [x for x in traci.edge.getIDList() if ":" not in x]

    # Retrieve number of north (or south) edges to retrieve number of cols
    # (divided by two as there are to edges per road)
    cols = len([x for x in valid_edges if "n" in x]) / 2
    # Retrieve number of west (or west) edges to retrieve number of rows
    # (divided by two as there are to edges per road)
    rows = len([x for x in valid_edges if "w" in x]) / 2

    return int(rows), int(cols)


# ROUTES UTILS
def retrieve_turn_prob_by_edge(traci, turn_prob: pd.DataFrame) -> dict:
    """
    Process the raw turn probabilities information and relate them to each edge of the network

    :param traci: TraCI instance
    :param turn_prob: raw turn probabilities information
    :type turn_prob: pandas DataFrame
    :return: turn probabilities by edge
    :rtype: dict
    """
    # Retrieve probabilities
    turn_prob_right, turn_prob_left, turn_prob_forward, edges_id = turn_prob.values.T.tolist()

    # Get all edges (remove those inner edges with ':')
    all_edges = [edge for edge in traci.edge.getIDList() if ':' not in edge]

    # Initialize dict
    prob_by_edges = {}
    # Turn probabilities are calculated as:
    # forward -> 0 to value; right -> forward to forward + value; left -> forward + right + value.
    # Example: forward = 0.60; right = 0.20; left = 0.20
    # Result: forward = 0.60; right = 0.80; left = 1.00
    if edges_id == 'all':  # Same probabilities to all roads
        for index, edge in enumerate(all_edges):
            # Store the probabilities
            prob_by_edges[edge] = {'turn_prob_right': float(turn_prob_right) + float(turn_prob_forward),
                                   'turn_prob_left': float(turn_prob_left) + float(turn_prob_right) +
                                                     float(turn_prob_forward),
                                   'turn_prob_forward': float(turn_prob_forward)}
    else:  # Specific probabilities
        # Retrieve each probability per specified edge
        turn_prob_right, turn_prob_left, turn_prob_forward, specific_edges = turn_prob_right.split(';'), \
                                                                             turn_prob_left.split(';'), \
                                                                             turn_prob_forward.split(';'), \
                                                                             edges_id.split(';')
        # Specific junctions
        for index, edge in enumerate(specific_edges):
            prob_by_edges[edge] = {'turn_prob_right': float(turn_prob_right[index]) +
                                                      float(turn_prob_forward[index]),
                                   'turn_prob_left': float(turn_prob_left[index]) +
                                                     float(turn_prob_forward[index]) +
                                                     float(turn_prob_right[index]),
                                   'turn_prob_forward': float(turn_prob_forward[index])}

        # Store default probabilities on those unspecified edges
        for index, edge in enumerate(list(set(all_edges) - set(specific_edges))):
            prob_by_edges[edge] = DEFAULT_TURN_DICT

    return prob_by_edges


def update_route_with_turns(traci, net_graph: NetGraph, traffic_lights: dict, turn_prob_by_edges: dict) -> None:
    """
    Update the vehicles routes based on the turn probabilities and count them

    :param traci: TraCI instance
    :param net_graph: network graph
    :type net_graph: NetGraph
    :param traffic_lights: dictionary with the traffic lights of the simulation
    :type traffic_lights: dict
    :param turn_prob_by_edges: dictionary with the probabilities of turning per edge
    :type turn_prob_by_edges: dict
    :return: None
    """
    # Get all vehicles from simulation
    vehicles = traci.vehicle.getIDList()

    # Iterate over the vehicles
    for vehicle in vehicles:
        # Get current vehicle road, origin and destination
        vehicle_road = traci.vehicle.getRoadID(vehicle)
        # Exclude inner edges
        if ':' not in vehicle_road:
            # Retrieve origin and destination junctions
            source, destination = vehicle_road.split('_')

            # Initialize variable to store the destination info
            graph_destination_info = None
            # Iterate over the possible destinations of the current junction
            for possible_destination in net_graph.graph.get(source):
                # Retrieve the information if its available
                if possible_destination['to'] == destination:
                    graph_destination_info = possible_destination['out_edge']
                    break

            # Retrieve next traffic light
            next_junction = destination if 'c' in destination else ''

            # Target edge and turn
            target_edge, turn = '', ''
            # Check if there is next traffic light, if the vehicle is not counted and the next junction info is
            # available
            if next_junction != '' and not \
                    traffic_lights[next_junction].is_vehicle_turning_counted(vehicle_id=vehicle) and \
                    graph_destination_info:
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
                target_edge = graph_destination_info[f'{source}_{destination}'][turn]

                # Calculate if the target edge is valid
                if target_edge != '':
                    # Retrieve vehicle type to find new route
                    cur_vehicle_type = traci.vehicle.getTypeID(vehicle)
                    # Find new route
                    new_route = traci.simulation.findRoute(fromEdge=vehicle_road, toEdge=target_edge,
                                                           vType=cur_vehicle_type).edges

                    # Check if there are routes available (from and to) based on the current vehicle type
                    if new_route:
                        # Set new route
                        traci.vehicle.setRoute(vehicle, new_route)

                        # Increase the TL turn counter
                        traffic_lights[next_junction].increase_turning_vehicles(turn)

                        # Add new vehicle
                        traffic_lights[next_junction].append_turning_vehicle(vehicle_id=vehicle)


def calculate_turning_vehicles(traci, net_graph: NetGraph, traffic_lights: dict) -> None:
    """
    Calculate the turning vehicles based on its route

    :param traci: TraCI instance
    :param net_graph: network graph
    :type net_graph: NetGraph
    :param traffic_lights: dictionary with the traffic lights of the simulation
    :type traffic_lights: dict
    :return: None
    """

    # Get all vehicles from simulation
    vehicles = traci.vehicle.getIDList()

    # Iterate over the vehicles
    for vehicle in vehicles:
        # Get next junction
        next_junction = traci.vehicle.getNextTLS(vehicle)
        # Get current vehicle road, origin and destination
        vehicle_road = traci.vehicle.getRoadID(vehicle)
        # Exclude inner edges and check if it has edges
        if ':' not in vehicle_road and next_junction:
            # Get closest junction
            next_junction = next_junction[0][0]
            # Check if vehicle is not counted
            if next_junction and not traffic_lights[next_junction].is_vehicle_turning_counted(vehicle_id=vehicle):
                # Retrieve vehicle route and current edge
                veh_route = traci.vehicle.getRoute(vehicle)
                cur_edge_index = traci.vehicle.getRouteIndex(vehicle)
                # It is not at the end of the simulation
                if cur_edge_index != len(veh_route):
                    # Get the current edge and junction
                    current_edge = veh_route[cur_edge_index]
                    current_junction = current_edge.split('_')[0]
                    # Retrieve next edge
                    next_edge = veh_route[cur_edge_index + 1]

                    # Retrieve possible turns from the source and next junctions
                    possible_turns = [destination['out_edge'] for destination in net_graph.graph[current_junction]
                                           if destination['to'] == next_junction][0]
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


# Simulation related utils
def process_payload(traffic_info: dict, date_info: dict) -> list:
    """
    Process the traffic_info and date_info dictionaries to be formatted to a valid Telegraf schema
    
    :param traffic_info: traffic information
    :type traffic_info: dict
    :param date_info: date information
    :type date_info: dict
    :return: Telegraf valid schema parsed information in a list
    :rtype: list
    """
    parsed_traffic_info = copy.deepcopy(traffic_info)

    if 'vehicles_passed' in parsed_traffic_info and 'turning_vehicles' in parsed_traffic_info:
        # Remove "vehicles_passed" key from traffic_info dict
        parsed_traffic_info.pop("vehicles_passed", None)
        # Remove also the "vehicles_passed" key from the turning vehicles
        parsed_traffic_info['turning_vehicles'].pop("vehicles_passed", None)

    traffic_info_payload = dict(**dict(parsed_traffic_info), **dict(date_info))

    return traffic_info_payload


def retrieve_date_info(timestep: int, time_pattern: pd.DataFrame) -> dict:
    """
    Retrieve the date information for a given timestep (day, date_day, date_month and date_year)
    
    :param timestep: simulation timestep
    :type timestep: int
    :param time_pattern: simulation traffic time pattern
    :type time_pattern: pandas Dataframe
    :return: information related to the traffic simulation date.
    :rtype: dict  
    """
    # Calculate the simulation timestep
    simulation_timestep = math.floor(timestep / TIMESTEPS_PER_HALF_HOUR)
    # Create the dict to store the information
    simulation_date_info = dict()

    # If simulation is not ended
    if simulation_timestep < len(time_pattern.pattern):

        # Obtain all the date information
        simulation_date_info = time_pattern.get_pattern_info(simulation_timestep=simulation_timestep,
                                                             fields=DATE_FIELDS)

        # Store default values if there are not defined
        if 'day' not in simulation_date_info:
            simulation_date_info['day'] = DEFAULT_DAY
        if 'date_day' not in simulation_date_info:
            simulation_date_info['date_day'] = DEFAULT_DATE_DAY
        if 'date_month' not in simulation_date_info:
            simulation_date_info['date_month'] = DEFAULT_DATE_MONTH
        if 'date_year' not in simulation_date_info:
            simulation_date_info['date_year'] = DEFAULT_DATE_YEAR

    return simulation_date_info


# Network graph related utils
def retrieve_turns_edges(net_graph: NetGraph, cols: int) -> dict:
    """
    Retrieve the turn edges for all the edges of the network topology
    
    :param net_graph: network topology graph
    :type net_graph: NetGraph
    :param cols: number of columns of the topology
    :type cols: int
    :return: turn edges for all the edges
    :rtype: dict
    """
    # Initialize edge dictionary
    edge_turns = {}

    # Iterate over the network graph nodes
    for node, value in net_graph.graph.items():
        # Iterate over each possible node destination
        for possible_destination in value:
            # Retrieve turn edges (right, left and forward) of outer edges
            for edge, out_edges in possible_destination['out_edge'].items():
                edge_turns.update(retrieve_edge_information(edge, out_edges, cols))
            # Retrieve turn edges (right, left and forward) of inner edges
            for edge, in_edges in possible_destination['in_edge'].items():
                edge_turns.update(retrieve_edge_information(edge, in_edges, cols))

    return edge_turns


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


def update_edge_turns_with_probs(edge_turns: dict, traffic_info: dict) -> dict:
    """
    Update the edge turns with the information related to the probabilities of turning to each road

    :param edge_turns: edge turns per edge
    :type edge_turns: dict
    :param traffic_info: traffic simulation information
    :type traffic_info: dict
    :return: updated edge turns with new turn probabilities
    :rtype: dict
    """
    for road, probs in traffic_info.items():
        edge_turns[road]['right']['prob'] = probs[0]
        edge_turns[road]['left']['prob'] = probs[1]
        edge_turns[road]['forward']['prob'] = probs[2]

    return edge_turns
