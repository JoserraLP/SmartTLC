# UTILS
import copy
import math

import pandas as pd

from sumo_generators.static.constants import DEFAULT_DATE_MONTH, DEFAULT_DATE_YEAR, DEFAULT_DATE_DAY, DEFAULT_DAY, \
    DATE_FIELDS, TIMESTEPS_PER_HALF_HOUR


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