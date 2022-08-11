import datetime
import random

import pandas as pd
import t_predictor.static.constants as cnt
from sumo_generators.static.constants import NUM_TRAFFIC_TYPES


def check_vacation(date: pd.DataFrame):
    """
    Check if a given date is in vacation range.
    * Summer vacation: from 20-07-2021 to 10-09-2021
    * Winter vacation: from 21-12-2020 to 7-1-2021 and from  21-12-2021 to 7-1-2022
    * Otherwise non vacation

    :param date: date with fields (date_year, date_month and date_day)
    :type date: pd.DataFrame
    :return: 0 if summer vacation, 1 if winter vacation, -1 otherwise.
    :rtype: int
    """
    # Calculate the current date
    current_date = datetime.date(year=date['date_year'], month=date['date_month'], day=date['date_day'])
    
    # Retrieve vacation dates
    start_summer_day, start_summer_month, start_summer_year = [int(x) for x in cnt.START_SUMMER_DATE.split('/')]
    end_summer_day, end_summer_month, end_summer_year = [int(x) for x in cnt.END_SUMMER_DATE.split('/')]
    start_winter_day, start_winter_month, start_winter_year = [int(x) for x in cnt.START_WINTER_DATE.split('/')]
    end_winter_day, end_winter_month, end_winter_year = [int(x) for x in cnt.END_WINTER_DATE.split('/')]
    
    # Check if summer
    if datetime.date(year=int(start_summer_year), month=start_summer_month, day=start_summer_day) <= current_date <= \
            datetime.date(year=end_summer_year, month=end_summer_month, day=end_summer_day):
        return 0  # Summer
    # Check if winter
    elif (datetime.date(year=start_winter_year-1, month=start_winter_month, day=start_winter_day) <= current_date 
          <= datetime.date(year=end_winter_year, month=end_winter_month, day=end_winter_day)) or \
            (datetime.date(year=start_winter_year, month=start_winter_month, day=start_winter_day) <= current_date 
             <= datetime.date(year=end_winter_year+1, month=end_winter_month, day=end_winter_day)):
        return 1  # Winter
    else:
        return -1  # Non-vacation


def append_dates_info(dataframe: pd.DataFrame, date: pd.DataFrame) -> pd.DataFrame:
    """
    Append date information into a dataframe

    :param dataframe: dataframe to append date to
    :type dataframe: pd.DataFrame
    :param date: date (represented in dataframe with values day, date_day, date_month, date_year) to append
    :type date: pd.DataFrame

    :return: dataframe with date added
    :rtype: pandas DataFrame
    """
    dataframe['day'] = date['day']
    dataframe['date_day'] = date['date_day']
    dataframe['date_month'] = date['date_month']
    dataframe['date_year'] = date['date_year']
    return dataframe


class TimePatternGenerator:
    """
    Class that generates the different flows of a SUMO simulation
    """

    def __init__(self, input_file: str = cnt.DEFAULT_CALENDAR_FILE):
        """
        TimePatternGenerator initializer
        """

        # Read dataframe from csv
        self._calendar = pd.read_csv(input_file, sep=';', header=0,
                                     usecols=['Dia', 'Dia_semana', 'laborable / festivo / domingo festivo'])
        # Set the different dataframe columns
        self._calendar.columns = ['date', 'day', 'festive']

        # Define the base temporal patterns
        self._base_patterns = {
            'festive': pd.read_csv(cnt.DEFAULT_TIME_PATTERNS_FOLDER + 'base_patterns/festive_day.csv', 
                                   usecols=['hour', 'traffic_type']),
            'friday': pd.read_csv(cnt.DEFAULT_TIME_PATTERNS_FOLDER + 'base_patterns/friday.csv', 
                                  usecols=['hour', 'traffic_type']),
            'monday': pd.read_csv(cnt.DEFAULT_TIME_PATTERNS_FOLDER + 'base_patterns/monday.csv', 
                                  usecols=['hour', 'traffic_type']),
            'saturday': pd.read_csv(cnt.DEFAULT_TIME_PATTERNS_FOLDER + 'base_patterns/saturday.csv', 
                                    usecols=['hour', 'traffic_type']),
            'summer_vacations_day': pd.read_csv(cnt.DEFAULT_TIME_PATTERNS_FOLDER + 
                                                'base_patterns/summer_vacations_day.csv', 
                                                usecols=['hour', 'traffic_type']),
            'sunday': pd.read_csv(cnt.DEFAULT_TIME_PATTERNS_FOLDER + 'base_patterns/sunday.csv', 
                                  usecols=['hour', 'traffic_type']),
            'thursday': pd.read_csv(cnt.DEFAULT_TIME_PATTERNS_FOLDER + 'base_patterns/thursday.csv', 
                                    usecols=['hour', 'traffic_type']),
            'tuesday': pd.read_csv(cnt.DEFAULT_TIME_PATTERNS_FOLDER + 'base_patterns/tuesday.csv', 
                                   usecols=['hour', 'traffic_type']),
            'wednesday': pd.read_csv(cnt.DEFAULT_TIME_PATTERNS_FOLDER + 'base_patterns/wednesday.csv', 
                                     usecols=['hour', 'traffic_type']),
            'winter_vacations_day': pd.read_csv(cnt.DEFAULT_TIME_PATTERNS_FOLDER + 
                                                'base_patterns/winter_vacations_day.csv',
                                                usecols=['hour', 'traffic_type']),
        }

        # Store working usual days
        self._working_days = ['monday', 'tuesday', 'friday', 'sunday', 'thursday', 'saturday', 'wednesday']

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

        # Obtain only the 2021 rows
        self._calendar = self._calendar[self._calendar['date_year'] == 2021]

        # Remove date column
        self._calendar = self._calendar.drop(columns=['date'])

        # Translate values
        self._calendar = self._calendar.replace({"day": cnt.TRANSLATE_DICT, "festive": cnt.TRANSLATE_DICT})

        # Append working to NaN festive
        self._calendar = self._calendar.fillna('working')

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
            # Initialize the base pattern to None to fill it
            base_pattern = None
            # Retrieve kind of vacation
            vacation_type = check_vacation(date)
            # We are going to append different values to each base pattern such as:
            # Append day, date_day, date_month and date_year
            if vacation_type == -1:
                if date['festive'] == 'festive':
                    # It is festive day
                    base_pattern = append_dates_info(self._base_patterns['festive'], date)
                else:
                    # It is usual day
                    base_pattern = append_dates_info(self._base_patterns[date['day']], date)
            else:
                # Summer vacation
                if vacation_type == 0:
                    base_pattern = append_dates_info(self._base_patterns['summer_vacations_day'], date)
                # Winter vacation
                elif vacation_type == 1:
                    base_pattern = append_dates_info(self._base_patterns['winter_vacations_day'], date)

            # If the base pattern is not empty, append it
            if base_pattern is not None:
                pattern_calendar = pattern_calendar.append(base_pattern, ignore_index=True)

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
            # Initialize the base pattern to None to fill it
            base_pattern = None

            # Retrieve kind of vacation
            vacation_type = check_vacation(date)

            # We are going to append different values to each base pattern such as:
            # Append day, date_day, date_month and date_year

            # It is usual or festive day
            if vacation_type == -1:
                # Retrieve random value for swapping vacation day.
                # 0: swap to summer vacation day
                # 1: swap to winter vacation day
                swap_usual_to_vacation_day = random.randint(0, cnt.RANDOM_USUAL_TO_VACATION_DAY_RANGE)
                # Swap a usual day as vacation
                if swap_usual_to_vacation_day == 0:
                    base_pattern = append_dates_info(self._base_patterns['summer_vacations_day'], date)
                elif swap_usual_to_vacation_day == 1:
                    base_pattern = append_dates_info(self._base_patterns['winter_vacations_day'], date)
                else:
                    # Retrieve the given pattern
                    if date['festive'] == 'festive':
                        base_pattern = append_dates_info(self._base_patterns['festive'], date)
                    else:
                        # Retrieve random value for swapping between usual days.
                        swap_usual_day = random.randint(0, cnt.RANDOM_USUAL_REPLACE)
                        # Swap value
                        if swap_usual_day == 0:
                            random_day_index = random.randint(0, len(self._working_days)-1)
                            random_day = self._working_days[random_day_index]
                            base_pattern = append_dates_info(self._base_patterns[random_day], date)
                        else:
                            base_pattern = append_dates_info(self._base_patterns[date['day']], date)
            # It is a vacation day
            else:
                # Retrieve random value for swapping usual day. 0: swap to usual day
                swap_vacation_to_usual_day = random.randint(0, cnt.RANDOM_VACATION_TO_USUAL_DAY_RANGE)

                # Retrieve random value to swap the type of vacation. 0: swap to opposite day
                swap_type_vacation_day = random.randint(0, cnt.RANDOM_VACATION_SWAP_RANGE)

                # Swap a vacation day as usual
                if swap_vacation_to_usual_day == 0:
                    base_pattern = append_dates_info(self._base_patterns[date['day']], date)
                # Summer vacation
                elif vacation_type == 0:
                    # Swap from summer to winter
                    if swap_type_vacation_day == 0:
                        base_pattern = append_dates_info(self._base_patterns['winter_vacations_day'], date)
                    # Leave as a summer day
                    else:
                        base_pattern = append_dates_info(self._base_patterns['summer_vacations_day'], date)
                # Winter vacation
                elif vacation_type == 1:
                    # Swap from winter to summer
                    if swap_type_vacation_day == 0:
                        base_pattern = append_dates_info(self._base_patterns['summer_vacations_day'], date)
                    # Leave as winter day
                    else:
                        base_pattern = append_dates_info(self._base_patterns['winter_vacations_day'], date)

            # If the base pattern is not empty, append it
            if base_pattern is not None:

                # Generate random variance on traffic type by getting a random hour range
                hour_index = random.randint(0, cnt.RANDOM_TRAFFIC_TYPE_RANGE)
                if hour_index < cnt.NUM_ROWS_PER_DAY:  # Valid hour random generation
                    # Generate the noise that will be applied to the traffic type field
                    noise_traffic_type = random.randint(cnt.RANDOM_TRAFFIC_TYPE_LOWER_BOUND,
                                                        cnt.RANDOM_TRAFFIC_TYPE_UPPER_BOUND)
                    # Retrieve the current traffic type
                    cur_traffic_type = base_pattern.loc[hour_index, 'traffic_type']

                    # Check if the new traffic type is in a valid range
                    if cur_traffic_type - abs(noise_traffic_type) < 0:
                        cur_traffic_type = 0
                    elif cur_traffic_type + abs(noise_traffic_type) > NUM_TRAFFIC_TYPES:
                        cur_traffic_type = 11
                    else:
                        cur_traffic_type = cur_traffic_type + noise_traffic_type

                    # Store the new traffic type
                    base_pattern.loc[hour_index, 'traffic_type'] = cur_traffic_type

                # Append the modified base pattern
                pattern_calendar = pattern_calendar.append(base_pattern, ignore_index=True)

        return pattern_calendar
