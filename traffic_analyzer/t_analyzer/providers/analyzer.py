import ast

import paho.mqtt.client as mqtt
from sumo_generators.static.constants import TRAFFIC_INFO_TOPIC, MQTT_PORT, MQTT_URL, TRAFFIC_ANALYSIS_TOPIC, \
    DEFAULT_TEMPORAL_WINDOW, FLOWS_VALUES
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
    """

    def __init__(self, mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT,
                 temporal_window: float = DEFAULT_TEMPORAL_WINDOW) -> None:
        """
        Traffic analyzer class initializer.
        """
        # High values
        self.high_vehs_per_hour = FLOWS_VALUES['high']['vehsPerHour']
        self.high_vehs_range = FLOWS_VALUES['high']['vehs_range']
        # Medium values
        self.med_vehs_per_hour = FLOWS_VALUES['med']['vehsPerHour']
        self.med_vehs_range = FLOWS_VALUES['med']['vehs_range']
        # Low values
        self.low_vehs_per_hour = FLOWS_VALUES['low']['vehsPerHour']
        self.low_vehs_range = FLOWS_VALUES['low']['vehs_range']
        # Very Low values
        self.very_low_vehs_per_hour = FLOWS_VALUES['very_low']['vehsPerHour']
        self.very_low_vehs_range = FLOWS_VALUES['very_low']['vehs_range']

        # Retrieve proportion value
        window_proportion = calculate_proportion_value(temporal_window=temporal_window)

        # Get traffic bounds
        self.very_low_lower_bound = 0
        self.very_low_upper_bound = round((self.very_low_vehs_per_hour + self.very_low_vehs_range) / window_proportion)
        self.low_upper_bound = round((self.low_vehs_per_hour + self.low_vehs_range) / window_proportion)
        self.med_upper_bound = round((self.med_vehs_per_hour + self.med_vehs_range) / window_proportion)
        self.high_upper_bound = round((self.high_vehs_per_hour + self.high_vehs_range) / window_proportion)

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
            # Subscribe to the traffic info topic from all traffic lights -> Append #
            self._mqtt_client.subscribe(TRAFFIC_INFO_TOPIC + '/#')

    def on_message(self, client, userdata, msg):
        """
        Callback called when the client receives a message from to the broker.

        :param client: MQTT client
        :param userdata: MQTT client data
        :param msg: message received from the middleware
        :return: None
        """
        # Parse message to dict
        traffic_info = ast.literal_eval(msg.payload.decode('utf-8'))

        # Retrieve junction id
        junction_id = str(msg.topic).split('/')[1] if '/' in msg.topic else ''

        # Check valid value
        if junction_id != '':
            # Analyze the current traffic and get the traffic type
            self._traffic_type = {junction_id: self.analyze_current_traffic_flow(
                passing_veh_n_s=int(traffic_info['passing_veh_n_s']),
                passing_veh_e_w=int(traffic_info['passing_veh_e_w']))}

            # Publish the message
            self._mqtt_client.publish(topic=TRAFFIC_ANALYSIS_TOPIC + '/' + junction_id,
                                      payload=parse_to_valid_schema(self._traffic_type))

    def analyze_current_traffic_flow(self, passing_veh_n_s: int, passing_veh_e_w: int) -> int:
        """
        Analyze the current traffic flow with the number of passing vehicles from both north-south and east-west.

        :param passing_veh_n_s: number of vehicles passing from north to south and vice versa.
        :type passing_veh_n_s: int
        :param passing_veh_e_w: number of vehicles passing from east to west and vice versa.
        :type passing_veh_e_w: int
        :return: traffic type
        :rtype: int
        """
        # Initialize the traffic type
        self._traffic_type = -1

        # Calculate the traffic type with the use of bounds (NS, EW).
        # Lower bound of a type is the highest bound of the previous one:
        if self.very_low_lower_bound <= passing_veh_n_s <= self.very_low_upper_bound \
                and self.very_low_lower_bound <= passing_veh_e_w <= self.very_low_upper_bound:
            self._traffic_type = 0  # (very_low, very_low)
        elif self.very_low_lower_bound <= passing_veh_n_s <= self.very_low_upper_bound <= passing_veh_e_w \
                <= self.low_upper_bound:
            self._traffic_type = 1  # (very_low, low)
        elif self.low_upper_bound >= passing_veh_n_s >= self.very_low_upper_bound >= passing_veh_e_w \
                >= self.very_low_lower_bound:
            self._traffic_type = 2  # (low, very_low)
        elif self.very_low_upper_bound <= passing_veh_n_s <= self.low_upper_bound \
                and self.very_low_upper_bound <= passing_veh_e_w <= self.low_upper_bound:
            self._traffic_type = 3  # (low, low)
        elif self.very_low_upper_bound <= passing_veh_n_s <= self.low_upper_bound <= passing_veh_e_w <= \
                self.med_upper_bound:
            self._traffic_type = 4  # (low, med)
        elif self.very_low_upper_bound <= passing_veh_n_s <= self.low_upper_bound and self.med_upper_bound <= \
                passing_veh_e_w <= self.high_upper_bound:
            self._traffic_type = 5  # (low, high)
        elif self.med_upper_bound >= passing_veh_n_s >= self.low_upper_bound >= passing_veh_e_w >= \
                self.very_low_upper_bound:
            self._traffic_type = 6  # (med, low)
        elif self.low_upper_bound <= passing_veh_n_s <= self.med_upper_bound and self.low_upper_bound <= \
                passing_veh_e_w <= self.med_upper_bound:
            self._traffic_type = 7  # (med, med)
        elif self.low_upper_bound <= passing_veh_n_s <= self.med_upper_bound <= passing_veh_e_w <= \
                self.high_upper_bound:
            self._traffic_type = 8  # (med, high)
        elif self.med_upper_bound <= passing_veh_n_s <= self.high_upper_bound and self.very_low_upper_bound <= \
                passing_veh_e_w <= self.low_upper_bound:
            self._traffic_type = 9  # (high, low)
        elif self.high_upper_bound >= passing_veh_n_s >= self.med_upper_bound >= passing_veh_e_w >= \
                self.low_upper_bound:
            self._traffic_type = 10  # (high, med)
        elif self.med_upper_bound <= passing_veh_n_s <= self.high_upper_bound and self.med_upper_bound <= \
                passing_veh_e_w <= self.high_upper_bound:
            self._traffic_type = 11  # (high, high)

        return self._traffic_type

    @property
    def traffic_type(self) -> int:
        """
        Analyzer traffic type

        :return: traffic type id
        :rtype: ind
        """
        return self._traffic_type
