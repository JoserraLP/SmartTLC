from t_analyzer.static.constants import FLOWS_VALUES, TRAFFIC_INFO_TOPIC, MQTT_PORT, MQTT_URL, ANALYZER_TOPIC
import paho.mqtt.client as mqtt
import ast


class TrafficAnalyzer:
    """
    Traffic analyzer class
    """

    def __init__(self, mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT) -> None:
        """
        Traffic analyzer class initializer.

        :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
        :type mqtt_url: str
        :param mqtt_port: MQTT middleware broker port. Default to 1883.
        :type mqtt_port: int
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

        # Get bounds, divided by 3 as it is the values it fits better the 5 minute window
        self.very_low_lower_bound = 0
        self.very_low_upper_bound = round((self.very_low_vehs_per_hour + self.very_low_vehs_range) / 3)
        self.low_upper_bound = round((self.low_vehs_per_hour + self.low_vehs_range) / 3)
        self.med_upper_bound = round((self.med_vehs_per_hour + self.med_vehs_range) / 3)
        self.high_upper_bound = round((self.high_vehs_per_hour + self.high_vehs_range) / 3)

        # Create the MQTT client, its callbacks and its connection to the broker
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self.on_connect
        self._mqtt_client.on_message = self.on_message
        self._mqtt_client.connect(mqtt_url, mqtt_port)
        self._mqtt_client.loop_forever()

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
            # Subscribe to the traffic info topic
            self._mqtt_client.subscribe(TRAFFIC_INFO_TOPIC)

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

        # Define analysis variable
        traffic_analysis = dict()

        # Iterate over the traffic lights
        for traffic_light_info in traffic_info:
            traffic_light_id = traffic_light_info['tl_id']

            # Remove summary information
            if traffic_light_info['tl_id'] != 'summary':

                # Analyze the current traffic and get the traffic type
                analyzed_type = self.analyze_current_traffic_flow(passing_veh_n_s=int(traffic_light_info['passing_veh_n_s']),
                                                                  passing_veh_e_w=int(traffic_light_info['passing_veh_e_w']))

                # Set the analysis into the published message
                traffic_analysis[traffic_light_id] = analyzed_type

        # Publish the message
        self._mqtt_client.publish(topic=ANALYZER_TOPIC, payload=str(traffic_analysis).replace('\'', '"')
                                  .replace(' ', ''))

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
        traffic_type = 0

        # Calculate the traffic type with the use of bounds.
        # Lower bound of a type is the highest bound of the previous one:
        if self.very_low_lower_bound <= passing_veh_n_s <= self.very_low_upper_bound and self.very_low_lower_bound <= \
                passing_veh_e_w <= self.very_low_upper_bound:
            traffic_type = 0
        elif self.very_low_lower_bound <= passing_veh_n_s <= self.very_low_upper_bound <= passing_veh_e_w \
                <= self.low_upper_bound:
            traffic_type = 1
        elif self.low_upper_bound >= passing_veh_n_s >= self.very_low_upper_bound >= passing_veh_e_w \
                >= self.very_low_lower_bound:
            traffic_type = 2
        elif self.very_low_upper_bound <= passing_veh_n_s <= self.low_upper_bound and self.very_low_upper_bound <= \
                passing_veh_e_w <= self.low_upper_bound:
            traffic_type = 3
        elif self.very_low_upper_bound <= passing_veh_n_s <= self.low_upper_bound <= passing_veh_e_w <= \
                self.med_upper_bound:
            traffic_type = 4
        elif self.very_low_upper_bound <= passing_veh_n_s <= self.low_upper_bound and self.med_upper_bound <= \
                passing_veh_e_w <= self.high_upper_bound:
            traffic_type = 5
        elif self.med_upper_bound >= passing_veh_n_s >= self.low_upper_bound >= passing_veh_e_w >= \
                self.very_low_upper_bound:
            traffic_type = 6
        elif self.low_upper_bound <= passing_veh_n_s <= self.med_upper_bound and self.low_upper_bound <= \
                passing_veh_e_w <= self.med_upper_bound:
            traffic_type = 7
        elif self.low_upper_bound <= passing_veh_n_s <= self.med_upper_bound <= passing_veh_e_w <= \
                self.high_upper_bound:
            traffic_type = 8
        elif self.med_upper_bound <= passing_veh_n_s <= self.high_upper_bound and self.very_low_upper_bound <= \
                passing_veh_e_w <= self.low_upper_bound:
            traffic_type = 9
        elif self.high_upper_bound >= passing_veh_n_s >= self.med_upper_bound >= passing_veh_e_w >= \
                self.low_upper_bound:
            traffic_type = 10
        elif self.med_upper_bound <= passing_veh_n_s <= self.high_upper_bound and self.med_upper_bound <= \
                passing_veh_e_w <= self.high_upper_bound:
            traffic_type = 11

        return traffic_type
