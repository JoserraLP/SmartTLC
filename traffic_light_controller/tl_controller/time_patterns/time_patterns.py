import math

import pandas as pd

from tl_controller.static.constants import DEFAULT_TIME_PATTERN_FILE, TIMESTEPS_PER_HALF_HOUR


class TimePattern:
    """
    Class for retrieving the different time patterns and use them into the simulation
    """

    def __init__(self, file_dir: str = DEFAULT_TIME_PATTERN_FILE):
        """
        TimePattern class initializer.

        :param file_dir: directory where the time pattern is located. Default to month.csv
        :type file_dir: str
        :return None
        """
        self._pattern = pd.read_csv(file_dir)

    def retrieve_turn_prob(self, timestep: int):
        """
        Retrieve the turn probabilities a time_pattern_id.

        :param timestep: current simulation time_pattern_id
        :type timestep: int
        :return: DataFrame with turn probabilities (right, left and forward)
        :rtype DataFrame
        """
        # Calculate the time pattern id
        time_pattern_id = math.floor(timestep / TIMESTEPS_PER_HALF_HOUR)

        if time_pattern_id < len(self._pattern):
            if 'turn_right' or 'turn_left' or 'turn_forward' in self._pattern.columns:
                # Index for those columns are 1,2 and 3 respectively
                return self._pattern.iloc[time_pattern_id, [1, 2, 3]]

    def get_num_sim(self):
        """
        Retrieve the number of simulations

        :return: number of simulations
        :rtype int
        """
        return len(self._pattern)

    def get_cur_hour(self, time_pattern_id: int):
        """
        Retrieve the current hour given a time_pattern_id.

        :param time_pattern_id: current simulation time_pattern_id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if 'hour' in self._pattern and time_pattern_id < len(self._pattern):
            return self._pattern.iloc[time_pattern_id]['hour']

    def get_cur_date_day(self, time_pattern_id: int):
        """
        Retrieve the simulation date day given a time_pattern_id.

        :param time_pattern_id: current simulation time_pattern_id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if 'date_day' in self._pattern and time_pattern_id < len(self._pattern):
            return self._pattern.iloc[time_pattern_id]['date_day']

    def get_cur_day(self, time_pattern_id: int):
        """
        Retrieve the simulation day given a time_pattern_id.

        :param time_pattern_id: current simulation time_pattern_id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if 'day' in self._pattern and time_pattern_id < len(self._pattern):
            return self._pattern.iloc[time_pattern_id]['day']

    def get_cur_week(self, time_pattern_id: int):
        """
        Retrieve the simulation week given a time_pattern_id.

        :param time_pattern_id: current simulation time_pattern_id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if 'date_week' in self._pattern and time_pattern_id < len(self._pattern):
            return self._pattern.iloc[time_pattern_id]['date_week']

    def get_cur_month(self, time_pattern_id: int):
        """
        Retrieve the simulation month given a time_pattern_id.

        :param time_pattern_id: current simulation id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if 'date_month' in self._pattern and time_pattern_id < len(self._pattern):
            return self._pattern.iloc[time_pattern_id]['date_month']

    def get_cur_year(self, time_pattern_id: int):
        """
        Retrieve the simulation year given a time_pattern_id.

        :param time_pattern_id: current simulation id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if 'date_year' in self._pattern and time_pattern_id < len(self._pattern):
            return self._pattern.iloc[time_pattern_id]['date_year']

    def retrieve_pattern_days(self, start_date, end_date):
        """
        Get the pattern selected by start day and end day.

        :param start_date: start time pattern day. Format is dd/mm/yyyy.
        :type start_date: str
        :param end_date: end time pattern day. Format is dd/mm/yyyy.
        :type end_date: str
        :return: Selected time pattern dataset
        :rtype: pd.DataFrame
        """
        # Get start and end dates
        start_day, start_month, start_year = start_date.split('/')
        end_day, end_month, end_year = end_date.split('/')

        # Get start date time pattern index
        start_index = self._pattern.index[(self._pattern['date_day'] == int(start_day)) &
                                          (self._pattern['date_month'] == int(start_month)) &
                                          (self._pattern['date_year'] == int(start_year))].tolist()[0]

        # Get end date time pattern index
        end_index = self._pattern.index[(self._pattern['date_day'] == int(end_day)) &
                                        (self._pattern['date_month'] == int(end_month)) &
                                        (self._pattern['date_year'] == int(end_year))].tolist()[-1]

        # Store the new time pattern by date
        self._pattern = self._pattern.iloc[start_index:end_index+1, :]

        # Reset index dataframe
        self._pattern.reset_index(drop=True, inplace=True)

        return self._pattern

    @property
    def pattern(self):
        """
        Pattern dataset getter

        :return: Time pattern dataset
        :rtype: pd.DataFrame
        """
        return self._pattern

    @pattern.setter
    def pattern(self, pattern):
        """
        Set the new pattern dataset

        :param pattern: Time pattern dataset
        :type: pd.DataFrame
        """
        self._pattern = pattern
