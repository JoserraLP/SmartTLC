import numpy as np
import pandas as pd
from influxdb_client import InfluxDBClient
import optparse
import time
import warnings

NUM_ITEMS_PER_DAY = 288
TEMPORAL_WINDOW_MINUTES = 5
DEFAULT_OUTPUT_FILE = "./data.xlsx"

# You can generate a Token from the "Tokens Tab" in the UI
TOKEN = "my-super-secret-auth-token"
ORG = "smarttlc"
BUCKET = "smarttlc"

client = InfluxDBClient(url="http://172.20.0.3:8086", token=TOKEN)

query_api = client.query_api()


def get_options():
    """
    Define options for the executable script.

    :return: options
    :rtype: object
    """
    optParser = optparse.OptionParser()
    optParser.add_option("-o", "--output-file", dest="output_file", action='store',
                         help="output file location")
    optParser.add_option("-w", "--waiting-time", dest="waiting_time", action='store', default=0,
                         help="waiting seconds to deploy. Use only when deploying Docker container. Default to 0")
    options, args = optParser.parse_args()
    return options


if __name__ == '__main__':
    # Remove warnings
    warnings.filterwarnings('ignore')

    # Retrieve execution options (parameters)
    exec_options = get_options()

    output_file = DEFAULT_OUTPUT_FILE

    if exec_options.output_file:
        output_file = exec_options.output_file

    # Sleep waiting time
    time.sleep(int(exec_options.waiting_time))

    # Query
    query = 'from(bucket: "{}")\
            |> range(start: -24h)\
            |> filter(fn: (r) => r["_field"] == "waiting_time_veh_e_w" \
            or r["_field"] == "waiting_time_veh_n_s" or r["_field"] == "passing_veh_e_w" \
            or r["_field"] == "passing_veh_n_s" or r["_field"] == "date_day" \
            or r["_field"] == "date_month" or r["_field"] == "date_year")'

    # using Table structure
    tables = query_api.query_data_frame(query.format(BUCKET), org=ORG)

    if not tables.empty:
        # Unused columns
        unused_columns = ["result", "table", "_start", "_stop", "_time", "host", "topic"]

        # Process the dataframe, removing unused columns
        tables = tables.drop(columns=unused_columns)

        # Rename columns
        rename_columns = {'_value': 'value', '_field': 'field', '_measurement': 'junction'}

        tables.rename(columns=rename_columns, inplace=True)

        # Remove summary rows
        tables = tables[tables['junction'] != 'summary']

        # Get number of junctions
        num_junctions = len(tables['junction'].unique())

        # Retrieve dates dataframe
        date_day = pd.concat([tables[tables['field'] == 'date_day']], ignore_index=True).reset_index()
        date_month = pd.concat([tables[tables['field'] == 'date_month']], ignore_index=True).reset_index()
        date_year = pd.concat([tables[tables['field'] == 'date_year']], ignore_index=True).reset_index()

        # 288 items per day -> Get number of days
        num_days = len(tables.loc[(tables['field'] == 'passing_veh_e_w')]) / (NUM_ITEMS_PER_DAY * num_junctions)

        # Get indexes from data
        indexes = [int(x * NUM_ITEMS_PER_DAY * num_days) for x in range(num_junctions)]

        # Retrieve hours list and parse it to dataframe. Time range are each 5 minutes
        hours = []
        for _ in range(int(num_days)*num_junctions):
            for x in range(24):
                for y in range(0, 60, TEMPORAL_WINDOW_MINUTES):
                    hour = "{x}:{y}"
                    if x < 10 and y < 10:
                        hour = hour.format(x='0' + str(x), y='0' + str(y))
                    elif x < 10:
                        hour = hour.format(x='0' + str(x), y=y)
                    elif y < 10:
                        hour = hour.format(x=x, y='0' + str(y))
                    else:
                        hour = hour.format(x=x, y=y)
                    hours.append(hour)

        hours = pd.DataFrame(hours)

        # Get sum of passing vehicles EW and NS
        passing_veh_ew = tables.loc[(tables['field'] == 'passing_veh_e_w')].reset_index()
        passing_veh_ns = tables.loc[(tables['field'] == 'passing_veh_n_s')].reset_index()

        # Get sum of waiting time EW and NS
        waiting_time_ew = tables.loc[(tables['field'] == 'waiting_time_veh_e_w')].reset_index()
        waiting_time_ns = tables.loc[(tables['field'] == 'waiting_time_veh_n_s')].reset_index()

        average_waiting_time = pd.DataFrame(columns=['value'])

        # Iterate over the indexes
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

        # Replace inf values by 0
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
        data.columns = ['date_day', 'date_month', 'date_year', 'hours', 'passing_veh_ew', 'passing_veh_ns',
                        'waiting_time_veh_ew', 'waiting_time_veh_ns', 'junction', 'average']

        # Add average waiting time
        data['average_waiting_time'] = average_waiting_time['value'].mean()

        # store the output excel
        data.to_excel(output_file, index=None, header=True)
