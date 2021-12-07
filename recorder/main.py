import argparse
import csv
import sys
from datetime import datetime

import paho.mqtt.client as mqtt

# MQTT VARIABLES
MQTT_URL = "172.20.0.2"
MQTT_PORT = 1883

# Default output file name
DEFAULT_OUTPUT_FILENAME = 'record_{}.csv'

# Datetime format
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# CSV Header
FIELDNAMES = ['topic', 'measurement_field', 'tag', 'timestamp']


class Recorder:
    """
    Class representing the recorder object that will store in a .csv file the system exchanged information related to
    contexts and observations.

    :param filename: Recorded output file
    :type filename: str
    :param mqtt_url: broker IP
    :type mqtt_url: str
    :param mqtt_port: broker port
    :type mqtt_port: int
    :param topics: middleware topics to subscribe to
    """

    def __init__(self, filename: str, mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT, topics=None) -> None:
        # Default mutable parameter
        if topics is None:
            self._topics = ['#']
        else:
            self._topics = topics

        # Open the output file as write only
        self._f = open(filename, 'w', encoding='UTF8')

        # Create a DictWriter in order to store the information on the file, split by ';'
        self._writer = csv.DictWriter(self._f, delimiter=";", fieldnames=FIELDNAMES, quoting=csv.QUOTE_ALL)

        # write the header (previously defined on the "fieldnames" parameter)
        self._writer.writeheader()

        # Create the MQTT client that will receive the data and set the required callbacks
        self._client = mqtt.Client()
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message

        # Connect the client to the broker
        self._client.connect(mqtt_url, mqtt_port)

    def loop_forever(self) -> None:
        """
        Calls the MQTT client loop forever and closes the output file descriptor.
        """
        self._client.loop_forever()
        self._f.close()

    def on_connect(self, client, userdata, flags, rc) -> None:
        """
        Define the callback for when the client receives a CONNACK response from the server and subscribes to all the
        topics available on the middleware.

        Subscribing in on_connect() means that if we lose the connection and reconnect then subscriptions will be
        renewed. Note that the parameters are not used but there are needed as it is a callback.

        :param client: mqtt client
        :param userdata: user data
        :param flags: connection flags
        :param rc: connection response code

        """

        # Subscribe to all the topics specified by parameters
        for topic in self._topics:
            self._client.subscribe(topic)

    def on_message(self, client, userdata, msg) -> None:
        """
        Define the callback for when a PUBLISH message is received from the server.

        :param client: mqtt client
        :param userdata: user data
        :param msg: message from server

        """

        # Split payload with ' ' char
        payload = msg.payload.decode("utf-8").split(' ')

        # Only save those messages that contains "sumo" and those with timestamp
        if any('sumo' in s for s in payload) and len(payload) > 2:
            # Get measurement and field data from payload (First position)
            measurement_field = payload[0]

            # Now we are going to retrieve the timestamp from the list of tags

            # Split data with ',' character in order to retrieve the list of tags
            payload_tag = payload[1].split(',')

            # Rejoin strings of payload, separated by comma, excluding timestamp
            tag = ','.join(payload_tag[:-1])

            # Extract timestamp, removing unnecessary characters
            timestamp = payload_tag[-1].replace('timestamp=\"', '') + ' ' + payload[2].replace('\"', '')

            # Write the data on the csv
            self._writer.writerow({FIELDNAMES[0]: msg.topic,
                                   FIELDNAMES[1]: measurement_field,
                                   FIELDNAMES[2]: tag,
                                   FIELDNAMES[3]: timestamp})


def get_options():
    """
    Get options from the execution command
    :return: Arguments options
    """
    # Create the Argument Parser
    argParser = argparse.ArgumentParser(description='Read info stored by the recorder and publish them into the '
                                                    'middleware broker based on its timestamp')

    # Define the arguments options
    argParser.add_argument("-o", "--output-file", dest="output_file", action="store", metavar="FILE",
                           type=str, default=DEFAULT_OUTPUT_FILENAME.format(datetime.utcnow().strftime(DATETIME_FORMAT))
                           , help="define the output file where the recorded data will be stored (.csv). "
                                  "By default generated in the execution folder and with name 'record_X.csv'")
    argParser.add_argument("-t", "--topics", dest="topics", action="store", default='#', type=str,
                           help="define the topics the recorder will be subscribed to, separated by comma ','")
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

    # Initialize recorder
    recorder = Recorder(filename=exec_options.output_file, mqtt_url=exec_options.broker_url,
                        mqtt_port=exec_options.broker_port, topics=exec_options.topics.split(','))

    # Loop forever on recorder for MQTT client
    recorder.loop_forever()
