import ast

import paho.mqtt.client as mqtt

from sumo_generators.static.constants import MQTT_PORT, MQTT_URL, TRAFFIC_ANALYSIS_TOPIC, \
    DEFAULT_TEMPORAL_WINDOW, FLOWS_VALUES, DEFAULT_TOPICS, DEFAULT_QOS, TRAFFIC_TYPES
from sumo_generators.utils.utils import parse_to_valid_schema


def calculate_proportion_value(temporal_window: float) -> float:
    """
    Calculates the value that will be used to divide the bounds in order to fit better to the actual traffic
    information. This is done based on the temporal window, as the bounds are related to the number of vehicles per
    hour.

    :param temporal_window: retrieval information
    :type temporal_window: float
    :return: proportion value
    :rtype: float
    """
    # TODO calculate with a more accurate formula
    # Now this formula outputs a value of 3 for a temporal window of 5 minutes, that is the used on the examples and
    # and the value that better fits
    # 15 is retrieved from 60/4, where the four value is selected by hand.
    return 15 / temporal_window


class TrafficAnalyzer:
    """
    Traffic analyzer class

    :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
    :type mqtt_url: str
    :param mqtt_port: MQTT middleware broker port. Default to 1883.
    :type mqtt_port: int
    :param temporal_window: monitoring temporal window. Default to 5.
    :type temporal_window: float
    :param topics: topics to subscribe to
    :type topics: list
    """

    def __init__(self, mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT,
                 temporal_window: float = DEFAULT_TEMPORAL_WINDOW, topics: list = DEFAULT_TOPICS) -> None:
        """
        Traffic analyzer class initializer.
        """
        # Retrieve topics
        self._topics = [(topic, DEFAULT_QOS) for topic in topics]

        # Retrieve proportion value
        window_proportion = calculate_proportion_value(temporal_window=temporal_window)

        # Get traffic bounds
        self.very_low_lower_bound = FLOWS_VALUES['very_low']['vehs_lower_limit']
        self.very_low_upper_bound = round(FLOWS_VALUES['very_low']['vehs_upper_limit'] / window_proportion)
        self.low_upper_bound = round(FLOWS_VALUES['low']['vehs_upper_limit'] / window_proportion)
        self.med_upper_bound = round(FLOWS_VALUES['med']['vehs_upper_limit'] / window_proportion)
        self.high_upper_bound = round(FLOWS_VALUES['high']['vehs_upper_limit'] / window_proportion)
        self.very_high_upper_bound = round(FLOWS_VALUES['very_high']['vehs_upper_limit'] / window_proportion)

        # Define traffic type
        self._traffic_type = 0

        # In case it is deployed, create the middleware connection
        if mqtt_url and mqtt_port:
            # Create the MQTT client, its callbacks and its connection to the broker
            self._mqtt_client = mqtt.Client()
            self._mqtt_client.on_connect = self.on_connect
            self._mqtt_client.on_message = self.on_message
            self._mqtt_client.connect(mqtt_url, mqtt_port)
            self._mqtt_client.loop_forever()
        else:
            self._mqtt_client = None

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback called when the client connects to the broker.

        :param client: MQTT client
        :param userdata: MQTT client data
        :param flags: MQTT connection flags
        :param rc: MQTT connection response code
        :return: None
        """
        if rc == 0:  # Connection established
            # Subscribe to specified topics
            self._mqtt_client.subscribe(self._topics)

    def on_message(self, client, userdata, msg):
        """
        Callback called when the client receives a message from to the broker.

        :param client: MQTT client
        :param userdata: MQTT client data
        :param msg: message received from the middleware
        :return: None
        """
        # Parse message to dict
        contextual_lanes_info = ast.literal_eval(msg.payload.decode('utf-8'))['info']

        # Iterate over the contextual lanes info
        for lane_info in contextual_lanes_info:
            # Create payload with the queue information and the traffic type analysis
            payload = {lane_info['lane']: self.analyze_current_traffic_flow(passing_veh=lane_info['num_passing_veh'])}
            # Publish the payload
            self._mqtt_client.publish(topic=TRAFFIC_ANALYSIS_TOPIC+'/'+lane_info['tl_id'],
                                      payload=parse_to_valid_schema(payload))

    def analyze_current_traffic_flow(self, passing_veh: int) -> int:
        """
        Analyze the current traffic flow with the number of passing vehicles.

        :param passing_veh: number of vehicles passing for a given queue
        :type passing_veh: int
        :return: traffic type
        :rtype: int
        """
        # Initialize the traffic type
        self._traffic_type = -1

        # Calculate the traffic type.
        # Lower bound of a type is the highest bound of the previous one:
        if self.very_low_lower_bound <= passing_veh <= self.very_low_upper_bound:
            self._traffic_type = TRAFFIC_TYPES['very_low']  # very_low
        elif self.very_low_upper_bound <= passing_veh <= self.low_upper_bound:
            self._traffic_type = TRAFFIC_TYPES['low']  # low
        elif self.low_upper_bound <= passing_veh <= self.med_upper_bound:
            self._traffic_type = TRAFFIC_TYPES['med']  # medium
        elif self.med_upper_bound <= passing_veh <= self.high_upper_bound:
            self._traffic_type = TRAFFIC_TYPES['high']  # high
        elif self.med_upper_bound <= passing_veh <= self.high_upper_bound:
            self._traffic_type = TRAFFIC_TYPES['very_high']  # very_high

        return self._traffic_type

    @property
    def traffic_type(self) -> int:
        """
        Analyzer traffic type

        :return: traffic type id
        :rtype: ind
        """
        return self._traffic_type
