import math

import pandas as pd
from sumo_generators.static.constants import TIMESTEPS_PER_HALF_HOUR, DEFAULT_TIME_PATTERN_FILE


class TimePattern:
    """
    Class for retrieving the different time patterns and use them into the simulation

    :param file_dir: directory where the time pattern is located. Default to month.csv
    :type file_dir: str
    """

    def __init__(self, file_dir: str = DEFAULT_TIME_PATTERN_FILE) -> None:
        """
        TimePattern class initializer.
        """
        self._pattern = pd.read_csv(file_dir)

    def retrieve_traffic_type(self, time_pattern_id: int) -> int:
        """
        Retrieve the traffic type given a time_pattern_id.

        :param time_pattern_id: current simulation time_pattern_id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if time_pattern_id < len(self._pattern):
            return self._pattern.loc[time_pattern_id]['traffic_type']

    def retrieve_turn_prob(self, simulation_timestep: int) -> pd.DataFrame:
        """
        Retrieve the turn probabilities given a simulation time step.

        :param simulation_timestep: current simulation time_pattern_id
        :type simulation_timestep: int
        :return: DataFrame with turn probabilities (right, left and forward)
        :rtype: DataFrame
        """
        # Calculate the time pattern id
        time_pattern_id = math.floor(simulation_timestep / TIMESTEPS_PER_HALF_HOUR)

        # If index is valid
        if time_pattern_id < len(self._pattern):
            # Retrieve turn probabilities
            if 'turn_right' or 'turn_left' or 'turn_forward' in self._pattern.columns:
                # Index for relevant columns (from 4 to the last columns) -> Turns fields
                return self._pattern.iloc[time_pattern_id, 4:]

    def get_pattern_info(self, simulation_timestep: int, fields: list) -> dict:
        """
        Retrieve the related date info given a simulation time step.

        :param simulation_timestep: current simulation time step
        :type simulation_timestep: int
        :param fields: date attributes to retrieve from the time pattern
        :type fields: list
        :return: pattern information
        :rtype: dict
        """
        if simulation_timestep < len(self._pattern):
            # First retrieve those columns that are not in the pattern, then retrieve those that are not in fields list
            actual_fields = set(fields) - (set(fields) - set(self._pattern.columns))
            # Obtain those columns that are on the dataframe
            return self._pattern.iloc[simulation_timestep][actual_fields].to_dict()

    def retrieve_pattern_days(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get the pattern selected by start day and end day.

        :param start_date: start time pattern day. Format is dd/mm/yyyy.
        :type start_date: str
        :param end_date: end time pattern day. Format is dd/mm/yyyy.
        :type end_date: str
        :return: Selected time pattern dataset from start to end dates
        :rtype: pd.DataFrame
        """
        # Get start and end dates
        start_day, start_month, start_year = start_date.split('/')
        end_day, end_month, end_year = end_date.split('/')

        # Get start date time pattern index, first item
        start_index = self._pattern.index[(self._pattern['date_day'] == int(start_day)) &
                                          (self._pattern['date_month'] == int(start_month)) &
                                          (self._pattern['date_year'] == int(start_year))].tolist()[0]

        # Get end date time pattern index, last item
        end_index = self._pattern.index[(self._pattern['date_day'] == int(end_day)) &
                                        (self._pattern['date_month'] == int(end_month)) &
                                        (self._pattern['date_year'] == int(end_year))].tolist()[-1]

        # Store the new time pattern by date -> +1 as the last index is not included
        self._pattern = self._pattern.iloc[start_index:end_index+1, :]

        # Reset index dataframe, dropping and replacing inplace
        self._pattern.reset_index(drop=True, inplace=True)

        return self._pattern

    @property
    def pattern(self) -> pd.DataFrame:
        """
        Pattern dataset getter

        :return: Time pattern dataset
        :rtype: pd.DataFrame
        """
        return self._pattern

    @pattern.setter
    def pattern(self, pattern: pd.DataFrame) -> None:
        """
        Set the new pattern dataset

        :param pattern: Time pattern dataset
        :type: pd.DataFrame
        :return: None
        """
        self._pattern = pattern
