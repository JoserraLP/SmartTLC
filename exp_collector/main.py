import argparse
import time
import warnings

import numpy as np
import pandas as pd
from influxdb_client import InfluxDBClient

# Define constants values related to data retrieval and InfluxDB variables
NUM_ITEMS_PER_DAY = 288
TEMPORAL_WINDOW_MINUTES = 5
DEFAULT_OUTPUT_FILE = "./data.xlsx"
TOKEN = "my-super-secret-auth-token"
ORG = "smarttlc"
BUCKET = "smarttlc"
DB_URL = "http://172.20.0.3:8086"


def get_options():
    """
    Get options for the executable script.

    :return: Arguments options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Script to collect an experiment information and store it on a '
                                                     'XLSX file.')

    # Define the arguments options
    arg_parser.add_argument("-o", "--output-file", dest="output_file", action='store', default=DEFAULT_OUTPUT_FILE,
                            help=f"define the output file location. Must be an XLSX file. "
                                 f"Default is {DEFAULT_OUTPUT_FILE}")
    
    arg_parser.add_argument("-w", "--waiting-time", dest="waiting_time", action='store', default=0,
                            help="waiting seconds to deploy. Use only when deploying Docker container. Default to 0")
    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == '__main__':
    # Remove warnings
    warnings.filterwarnings('ignore')

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Sleep process specified waiting time
    time.sleep(int(exec_options.waiting_time))

    # Define connection to InfluxDB database
    client = InfluxDBClient(url=DB_URL, token=TOKEN)

    # Retrieve the query InfluxDB API
    query_api = client.query_api()

    # Define the query
    query = 'from(bucket: "{}")\
            |> range(start: -24h)\
            |> filter(fn: (r) => r["_field"] == "waiting_time_veh_e_w" \
            or r["_field"] == "waiting_time_veh_n_s" or r["_field"] == "passing_veh_e_w" \
            or r["_field"] == "passing_veh_n_s" or r["_field"] == "date_day" \
            or r["_field"] == "date_month" or r["_field"] == "date_year")'

    # Parsing the query results to a Pandas DataFrame
    results = query_api.query_data_frame(query.format(BUCKET), org=ORG)

    # Check if there are results
    if not results.empty:
        # Define unused columns
        unused_columns = ["result", "table", "_start", "_stop", "_time", "host", "topic"]

        # Removing unused columns
        results = results.drop(columns=unused_columns)

        # Rename columns
        rename_columns = {'_value': 'value', '_field': 'field', '_measurement': 'junction'}
        results.rename(columns=rename_columns, inplace=True)

        # Remove summary rows
        results = results[results['junction'] != 'summary']

        # Get number of junctions
        num_junctions = len(results['junction'].unique())

        # Retrieve dataframe per days, month and year
        date_day = pd.concat([results[results['field'] == 'date_day']], ignore_index=True).reset_index()
        date_month = pd.concat([results[results['field'] == 'date_month']], ignore_index=True).reset_index()
        date_year = pd.concat([results[results['field'] == 'date_year']], ignore_index=True).reset_index()

        # 288 items per day -> Get number of days with information
        num_days = len(results.loc[(results['field'] == 'passing_veh_e_w')]) / (NUM_ITEMS_PER_DAY * num_junctions)

        # Get indexes from data
        indexes = [int(x * NUM_ITEMS_PER_DAY * num_days) for x in range(num_junctions)]

        # Retrieve hours list and parse it to dataframe. Time range are each 5 minutes
        hours = []
        # Iterate over the items of a day and a given junction
        for _ in range(int(num_days) * num_junctions):
            # Iterate over the hours of a day
            for x in range(24):
                # Iterate over the minutes by the temporal window
                for y in range(0, 60, TEMPORAL_WINDOW_MINUTES):
                    hour = "{x}:{y}"
                    # Format the hour and minutes based on the data information
                    if x < 10 and y < 10:
                        hour = hour.format(x='0' + str(x), y='0' + str(y))
                    elif x < 10:
                        hour = hour.format(x='0' + str(x), y=y)
                    elif y < 10:
                        hour = hour.format(x=x, y='0' + str(y))
                    else:
                        hour = hour.format(x=x, y=y)
                    # Append to the list of hours
                    hours.append(hour)

        # Parse hour list to a DataFrame
        hours = pd.DataFrame(hours)

        # Get sum of passing vehicles EW and NS
        passing_veh_ew = results.loc[(results['field'] == 'passing_veh_e_w')].reset_index()
        passing_veh_ns = results.loc[(results['field'] == 'passing_veh_n_s')].reset_index()

        # Get sum of waiting time EW and NS
        waiting_time_ew = results.loc[(results['field'] == 'waiting_time_veh_e_w')].reset_index()
        waiting_time_ns = results.loc[(results['field'] == 'waiting_time_veh_n_s')].reset_index()

        # Define DataFrame to store the average values
        average_waiting_time = pd.DataFrame(columns=['value'])

        # Iterate over the different number of items per day
        for i in range(NUM_ITEMS_PER_DAY):
            value = 0
            # Iterate over different junctions
            for index in indexes:
                # Calculate the total waiting time and total number of passing vehicles
                total_waiting_time = waiting_time_ew.iloc[index + i]['value'] + waiting_time_ns.iloc[index + i]['value']
                total_passing_veh = passing_veh_ew.iloc[index + i]['value'] + passing_veh_ns.iloc[index + i]['value']

                # Retrieve value -> Avoid division by zero
                if total_passing_veh != 0:
                    value += total_waiting_time / total_passing_veh

            # Append the average waiting time value
            average_waiting_time = average_waiting_time.append({'value': value}, ignore_index=True)

        # Replace infinite values by 0
        average_waiting_time = average_waiting_time.replace(np.inf, 0)

        # Process the data to set columns by info
        data = pd.DataFrame(data=pd.concat([date_day['value'],
                                            date_month['value'],
                                            date_year['value'],
                                            hours,
                                            passing_veh_ew['value'],
                                            passing_veh_ns['value'],
                                            waiting_time_ew['value'],
                                            waiting_time_ns['value'],
                                            passing_veh_ns['junction'],
                                            average_waiting_time['value']], axis=1))
        # Set the data columns
        data.columns = ['date_day', 'date_month', 'date_year', 'hours', 'passing_veh_e_w', 'passing_veh_n_s',
                        'waiting_time_veh_e_w', 'waiting_time_veh_n_s', 'junction', 'average']

        # Calculate average waiting time mean value
        data['average_waiting_time'] = average_waiting_time['value'].mean()

        # Store the output file
        data.to_excel(exec_options.output_file, index=None, header=True)
