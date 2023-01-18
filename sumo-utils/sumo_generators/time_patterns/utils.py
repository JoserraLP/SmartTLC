import math

from sumo_generators.static.constants import *


def retrieve_date_info(timestep: int, time_pattern) -> dict:
    """
    Retrieve date information related to a row from the time pattern.

    Information is: day, date_day, date_month, date_year.

    :param timestep: timestep of the row
    :type timestep: int
    :param time_pattern: time pattern dataset
    :return: dictionary with the date information
    """
    # Calculate the time pattern id
    simulation_timestep = math.floor(timestep / TIMESTEPS_PER_HOUR)

    # Initialize variable
    simulation_date_info = dict()

    # Check if timestep is in the time pattern
    if simulation_timestep < len(time_pattern.pattern):

        # Obtain all the date information
        simulation_date_info = time_pattern.get_pattern_info(simulation_timestep=simulation_timestep,
                                                             fields=DATE_FIELDS)

        # Store default values
        if 'day' not in simulation_date_info:
            simulation_date_info['day'] = DEFAULT_DAY
        if 'date_day' not in simulation_date_info:
            simulation_date_info['date_day'] = DEFAULT_DATE_DAY
        if 'date_month' not in simulation_date_info:
            simulation_date_info['date_month'] = DEFAULT_DATE_MONTH
        if 'date_year' not in simulation_date_info:
            simulation_date_info['date_year'] = DEFAULT_DATE_YEAR

    return simulation_date_info
