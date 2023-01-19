from os import listdir
from os.path import isfile, join
import random

import pandas as pd

import t_predictor.static.constants as cnt
from sumo_generators.static.constants import NUM_TRAFFIC_TYPES


def append_dates_info(dataframe: pd.DataFrame, date: pd.Series) -> pd.DataFrame:
    """
    Append date information into a dataframe

    :param dataframe: dataframe to append date to
    :type dataframe: pd.DataFrame
    :param date: date (represented in series with values day, date_day, date_month, date_year) to append
    :type date: pd.Series

    :return: dataframe with date added
    :rtype: pandas DataFrame
    """
    dataframe['day'] = date['day']
    dataframe['date_day'] = date['date_day']
    dataframe['date_month'] = date['date_month']
    dataframe['date_year'] = date['date_year']
    return dataframe


def get_base_patterns_filenames() -> list:
    """
    Retrieve the base time patterns names removing its extension

    :return: list with base patterns files names
    :rtype: list
    """
    return [f.split('.')[0] for f in listdir(cnt.DEFAULT_BASE_TIME_PATTERNS_FOLDER)
            if isfile(join(cnt.DEFAULT_BASE_TIME_PATTERNS_FOLDER, f))]


class TimePatternGenerator:
    """
    Class that generates the different flows of a SUMO simulation
    """

    def __init__(self, input_file: str):
        """
        TimePatternGenerator initializer
        """

        # Read dataframe from csv
        self._calendar = pd.read_csv(input_file, sep=',', dtype={'date': str, 'day': str, 'type': int})

        # Define base pattern cols
        base_pattern_cols = ['hour', 'traffic_type']

        # Get list of patterns
        base_patterns_filenames = get_base_patterns_filenames()

        # Define the base temporal patterns
        self._base_patterns = {filename: pd.read_csv(cnt.DEFAULT_BASE_TIME_PATTERNS_FOLDER + filename + '.csv',
                                                     usecols=base_pattern_cols)
                               for filename in base_patterns_filenames}

    def parse_calendar(self) -> None:
        """
        Parse the unnecessary columns and rows from the calendar dataframe.
        The parsed values are:

        * Delete rows with date as NaN.
        * Create different columns per day, month and year.
        * Remove all the data that is not from the year 2021.
        * Drop the 'date' column.
        * Translate the values from spanish to english.
        * Fill NaN values of 'festive' column with 'working' value.

        :return: None
        """
        # Remove invalid rows
        self._calendar = self._calendar.dropna(subset=['date'])

        # Retrieve and split date columns
        date = self._calendar['date'].str.split('/')
        self._calendar['date_day'] = date.str[0].astype(int)
        self._calendar['date_month'] = date.str[1].astype(int)
        self._calendar['date_year'] = date.str[2].astype(int)

        # Remove date column
        self._calendar = self._calendar.drop(columns=['date'])

    def get_pattern_calendar(self) -> pd.DataFrame:
        """
        Creates the calendar with the traffic type patterns.

        :return: calendar pattern dataset
        :rtype: pandas DataFrame
        """
        # Create pattern calendar
        pattern_calendar = pd.DataFrame()

        # Iterate over the calendar
        for index, date in self._calendar.iterrows():
            # First check specific dates such as first year day or Christmas.
            if date['date_day'] == 1 and date['date_month'] == 1:
                base_pattern = append_dates_info(self._base_patterns['first_year_day'], date)
            elif date['date_day'] == 25 and date['date_month'] == 12:
                base_pattern = append_dates_info(self._base_patterns['christmas_day'], date)
            else:
                # Check if bank holiday
                if date['type'] == 1:
                    base_pattern = append_dates_info(self._base_patterns['bank_holiday'], date)
                else:
                    # Check weekend days
                    if date['day'] in ['saturday', 'sunday']:
                        base_pattern = append_dates_info(self._base_patterns['weekend_day'], date)
                    # Other working days
                    else:
                        base_pattern = append_dates_info(self._base_patterns['working_day'], date)

            # If the base pattern is not empty, append it
            if base_pattern is not None:
                pattern_calendar = pd.concat([pattern_calendar, base_pattern], ignore_index=True)

        return pattern_calendar

    def get_random_pattern_calendar(self) -> pd.DataFrame:
        """
        Creates the calendar with the traffic type patterns adding some randomness.
        :return: calendar pattern dataset
        :rtype: pandas DataFrame
        """
        # Create pattern calendar
        pattern_calendar = pd.DataFrame()

        # Iterate over the calendar
        for index, date in self._calendar.iterrows():
            # First check specific dates such as first year day or Christmas.
            if date['date_day'] == 1 and date['date_month'] == 1:
                base_pattern = append_dates_info(self._base_patterns['first_year_day'], date)
            elif date['date_day'] == 25 and date['date_month'] == 12:
                base_pattern = append_dates_info(self._base_patterns['christmas_day'], date)
            else:
                # Check if bank holiday
                if date['type'] == 1:
                    base_pattern = append_dates_info(self._base_patterns['bank_holiday'], date)
                else:
                    # Check weekend days
                    if date['day'] in ['saturday', 'sunday']:
                        # Retrieve random value for swapping weekend day.
                        # 1: swap to working day
                        # Otherwise: do not swap
                        swap_to_working_day = random.randint(0, cnt.RANDOM_WEEKEND_TO_WORKING_SWAP_RANGE)
                        if swap_to_working_day == 1:
                            base_pattern = append_dates_info(self._base_patterns['working_day'], date)
                        else:
                            base_pattern = append_dates_info(self._base_patterns['weekend_day'], date)
                    # Other working days
                    else:
                        # Retrieve random value for swapping working day.
                        # 1: swap to weekend day
                        # 2: swap to bank holiday
                        # Otherwise: do not swap
                        swap_to_other_day = random.randint(0, cnt.RANDOM_WORKING_TO_OTHER_SWAP_RANGE)
                        if swap_to_other_day == 1:
                            base_pattern = append_dates_info(self._base_patterns['weekend_day'], date)
                        elif swap_to_other_day == 2:
                            base_pattern = append_dates_info(self._base_patterns['bank_holiday'], date)
                        else:
                            base_pattern = append_dates_info(self._base_patterns['working_day'], date)

            # If the base pattern is not empty
            if base_pattern is not None:
                # Generate random variance on traffic type
                # First getting a random hour
                hour_index = random.randint(0, cnt.RANDOM_TRAFFIC_TYPE_RANGE)
                # Valid hour random generation
                if hour_index < cnt.NUM_ROWS_PER_DAY:
                    # Generate the noise that will be applied to the traffic type field
                    noise_traffic_type = random.randint(cnt.RANDOM_TRAFFIC_TYPE_LOWER_BOUND,
                                                        cnt.RANDOM_TRAFFIC_TYPE_UPPER_BOUND)

                    # Retrieve the current traffic type
                    cur_traffic_type = base_pattern.loc[hour_index, 'traffic_type']

                    # Check if the new traffic type is in a valid range
                    if cur_traffic_type - abs(noise_traffic_type) < 0:
                        cur_traffic_type = 0
                    elif cur_traffic_type + abs(noise_traffic_type) > NUM_TRAFFIC_TYPES:
                        cur_traffic_type = NUM_TRAFFIC_TYPES
                    else:
                        cur_traffic_type = cur_traffic_type + noise_traffic_type

                    # Store the new traffic type
                    base_pattern.loc[hour_index, 'traffic_type'] = cur_traffic_type

                # Store it to the calendar
                pattern_calendar = pd.concat([pattern_calendar, base_pattern], ignore_index=True)

        return pattern_calendar
