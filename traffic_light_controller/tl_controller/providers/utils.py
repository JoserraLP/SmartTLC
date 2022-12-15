# UTILS
import copy
import math

import pandas as pd
from sumo_generators.static.constants import DEFAULT_DATE_MONTH, DEFAULT_DATE_YEAR, DEFAULT_DATE_DAY, DEFAULT_DAY, \
    DATE_FIELDS, TIMESTEPS_PER_HALF_HOUR, DEFAULT_TURN_DICT


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
            prob_by_edges[edge] = {'turn_prob_right': float(turn_prob_right[index]) + float(turn_prob_forward[index]),
                                   'turn_prob_left': float(turn_prob_left[index]) + float(turn_prob_forward[index]) +
                                                     float(turn_prob_right[index]),
                                   'turn_prob_forward': float(turn_prob_forward[index])}

        # Store default probabilities on those unspecified edges
        for index, edge in enumerate(list(set(all_edges) - set(specific_edges))):
            prob_by_edges[edge] = DEFAULT_TURN_DICT

    return prob_by_edges


# Simulation related utils
def process_payload(traffic_info: dict, date_info: dict) -> dict:
    """
    Process the traffic_info and date_info dictionaries to be formatted to a valid Telegraf schema
    
    :param traffic_info: traffic information
    :type traffic_info: dict
    :param date_info: date information
    :type date_info: dict
    :return: Telegraf valid schema parsed information in a dict
    :rtype: dict
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
