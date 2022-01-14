import argparse
import time

import numpy as np
import paho.mqtt.client as mqtt
import pandas as pd

# MQTT VARIABLES
MQTT_URL = "172.20.0.2"
MQTT_PORT = 1883

# Default output file name
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

# CSV Header
FIELDNAMES = ['topic', 'data', 'timestamp']


class Player:
    """
    Class representing the play object that will publish the information stored by the recorder, along with the temporal
    difference between messages, as they has been produced by the different components of the architecture.

    :param filename: Recorded input file
    :type filename: str
    :param mqtt_url: broker IP
    :type mqtt_url: str
    :param mqtt_port: broker port
    :type mqtt_port: int
    :param player_info: kind of information to be published. Options are: context, observation or qos.
    """

    def __init__(self, filename: str, mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT, player_info=None) -> None:
        # Open the input file and store the data in a pandas dataframe
        # Data is split by ';'
        self._data = pd.read_csv(filename, sep=';')

        # Create the MQTT client that will publish the data
        self._client = mqtt.Client()

        # Connect the client to the broker
        self._client.connect(mqtt_url, mqtt_port)

        # Store player info
        self._player_info = player_info

    def sort_data(self, field: str = 'timestamp') -> None:
        """
        Sort the data by the field indicated by parameters
        :param field: dataframe column that will be sorted by
        """
        self._data = self._data.sort_values(field, ignore_index=True)

    def process_timestamp(self) -> None:
        """
        Process the timestamp column on the dataframe and create a column that stores the ms needed to spend waiting
        in order to behave as the original information trip.
        """

        # Format the column 'timestamp' to represent seconds
        self._data['timestamp'] = pd.to_datetime(self._data['timestamp'], unit='s')

        # Calculate the temporal difference between adjacent rows
        self._data['timestamp_diff'] = self._data['timestamp'].diff().apply(lambda x: x / np.timedelta64(1, 'ms')) \
            .fillna(0).astype('int64')

        # Include first element as 0 due to the diff() method inserts an invalid value on the first position
        self._data.loc[0, 'timestamp_diff'] = 0

    def publish_all_data(self) -> None:
        """
        Publish the data with the given timestamp
        """

        # Sort dataframe by timestamp in order to assure the temporal order.
        self.sort_data(field='timestamp')

        # Process the timestamp field
        self.process_timestamp()

        # Iterate over all the rows
        for index, row in self._data.iterrows():
            # Retrieve the timestamp difference value
            sleep_time = row['timestamp_diff']

            # If the difference value is greater than 0 it means that the process has to be sleep this amount of time
            if sleep_time:
                # Sleep the process the sleep time seconds (divided by 1000 because is in milliseconds)
                time.sleep(sleep_time / 1000)

            # Publish message
            self._client.publish(topic=row['topic'], payload=row['data'])

        # Disconnect
        self._client.disconnect()


def get_options():
    """
    Get options from the execution command
    :return: Arguments options
    """
    # Create the Argument Parser
    argParser = argparse.ArgumentParser(description='Read info stored by the recorder and publish them into the '
                                                    'middleware broker based on its timestamp')

    # Define the arguments options
    argParser.add_argument("-i", "--input-file", dest="input_file", action="store", metavar="FILE", type=open,
                           help="define the input file where the data is stored (.csv)", required=True)
    argParser.add_argument("-d", "--data", dest="data", action="store", type=str,
                           help="define the kind of data that will be published split by comma. "
                                "It can be: context, observations or qos. Empty for all kind of data. ")
    argParser.add_argument("-b", "--broker-url", dest="broker_url", action="store", default=MQTT_URL, type=str,
                           help="define the broker url where the data will be published")
    argParser.add_argument("-p", "--broker-port", dest="broker_port", action="store", default=MQTT_PORT, type=int,
                           help="define the broker port")

    # Retrieve the arguments parsed
    args = argParser.parse_args()
    return args


if __name__ == "__main__":

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Initialize the player
    player = Player(filename=exec_options.input_file, mqtt_url=exec_options.broker_url,
                    mqtt_port=exec_options.broker_port, player_info=exec_options.data)

    # Publish all the data stored in the player
    player.publish_all_data()
