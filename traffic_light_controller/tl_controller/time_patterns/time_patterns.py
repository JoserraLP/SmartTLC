import pandas as pd

from tl_controller.static.constants import DEFAULT_TIME_PATTERN_FILE


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

    def retrieve_traffic_type(self, time_pattern_id: int):
        """
        Retrieve the traffic type given a time_pattern_id.

        :param time_pattern_id: current simulation time_pattern_id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if time_pattern_id < len(self._pattern):
            return self._pattern.loc[time_pattern_id]['traffic_type']

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
            return self._pattern.loc[time_pattern_id]['hour']

    def get_cur_date_day(self, time_pattern_id: int):
        """
        Retrieve the simulation date day given a time_pattern_id.

        :param time_pattern_id: current simulation time_pattern_id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if 'date_day' in self._pattern and time_pattern_id < len(self._pattern):
            return self._pattern.loc[time_pattern_id]['date_day']

    def get_cur_day(self, time_pattern_id: int):
        """
        Retrieve the simulation day given a time_pattern_id.

        :param time_pattern_id: current simulation time_pattern_id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if 'day' in self._pattern and time_pattern_id < len(self._pattern):
            return self._pattern.loc[time_pattern_id]['day']

    def get_cur_week(self, time_pattern_id: int):
        """
        Retrieve the simulation week given a time_pattern_id.

        :param time_pattern_id: current simulation time_pattern_id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if 'date_week' in self._pattern and time_pattern_id < len(self._pattern):
            return self._pattern.loc[time_pattern_id]['date_week']

    def get_cur_month(self, time_pattern_id: int):
        """
        Retrieve the simulation month given a time_pattern_id.

        :param time_pattern_id: current simulation id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if 'date_month' in self._pattern and time_pattern_id < len(self._pattern):
            return self._pattern.loc[time_pattern_id]['date_month']

    def get_cur_year(self, time_pattern_id: int):
        """
        Retrieve the simulation year given a time_pattern_id.

        :param time_pattern_id: current simulation id
        :type time_pattern_id: int
        :return: traffic type represented as an int
        :rtype int
        """
        if 'date_year' in self._pattern and time_pattern_id < len(self._pattern):
            return self._pattern.loc[time_pattern_id]['date_year']

    @property
    def pattern(self):
        """
        Return the pattern dataset

        :return: Time pattern dataset
        :rtype: pd.DataFrame
        """
        return self._pattern
