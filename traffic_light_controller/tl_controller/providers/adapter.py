from tl_controller.static.constants import TRAFFIC_TYPE_TL_ALGORITHMS, ERROR_THRESHOLD, MQTT_URL, MQTT_PORT, \
    PREDICTION_TOPIC, ANALYSIS_TOPIC, NUM_TRAFFIC_TYPES
import paho.mqtt.client as mqtt
import ast


class TrafficLightAdapter:
    """
    Traffic Light Adapter class
    """

    def __init__(self, traffic_prediction=None, traffic_analysis=None, mqtt_url: str = MQTT_URL,
                 mqtt_port: int = MQTT_PORT):
        """
        TraCISimulator initializer.

        :param traffic_prediction: traffic prediction dict. Default is None.
        :type traffic_prediction: dict
        :param traffic_analysis: traffic analysis dict. Default is None.
        :type traffic_analysis: dict
        :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
        :type mqtt_url: str
        :param mqtt_port: MQTT middleware broker port. Default to 1883.
        :type mqtt_port: int
        """
        # Store traffic prediction and analysis
        self._traffic_prediction = traffic_prediction
        self._traffic_analysis = traffic_analysis

        # Create the MQTT client, its callbacks and its connection to the broker
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self.on_connect
        self._mqtt_client.on_message = self.on_message
        self._mqtt_client.connect(mqtt_url, mqtt_port)
        self._mqtt_client.loop_start()

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
            # Subscribe to the traffic prediction and analysis topic
            self._mqtt_client.subscribe(PREDICTION_TOPIC)
            self._mqtt_client.subscribe(ANALYSIS_TOPIC)

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

        # Check the topic it comes from
        if msg.topic == PREDICTION_TOPIC:
            # Retrieve predicted traffic type
            self._traffic_prediction = traffic_info
        if msg.topic == ANALYSIS_TOPIC:
            # Retrieve analyzed traffic type
            self._traffic_analysis = traffic_info

    def get_new_tl_program(self):
        """
        Retrieve the new traffic light program based on the analyzer, predictor or both.

        :return: new tl program per traffic light
        :rtype: dict
        """

        # If only analyzer is deployed
        if self._traffic_analysis and not self._traffic_prediction:
            current_traffic_type = self._traffic_analysis
        # If only predictor is deployed
        elif self._traffic_prediction and not self._traffic_analysis:
            current_traffic_type = self._traffic_prediction
        else:
            current_traffic_type = dict()
            # If both analyzer and predictor are deployed
            if self._traffic_analysis and self._traffic_prediction:
                # It is chosen the traffic_analysis but can be used both as they have the same information
                for traffic_light in self._traffic_analysis.keys():

                    # Calculate the difference between the traffic types
                    error_distance = self._traffic_analysis[traffic_light] \
                                     - self._traffic_prediction[traffic_light]
                    # If the distance is less than the threshold
                    if abs(error_distance) <= ERROR_THRESHOLD:
                        # The analyzer is right, use its value
                        current_traffic_type[traffic_light] = self._traffic_analysis[traffic_light]
                    # Otherwise calculate the weighted value
                    else:
                        # 1/3 closest to the analyzer as it is in real time
                        new_traffic_type = self._traffic_analysis[traffic_light]\
                                           - int(error_distance / 3)
                        if new_traffic_type >= 0 or new_traffic_type <= NUM_TRAFFIC_TYPES:
                            # If calculated value is valid, store it
                            current_traffic_type[traffic_light] = new_traffic_type

        adapter_tl_programs = dict()

        if current_traffic_type is not None:
            # If the traffic type exists get the new traffic light program per traffic light
            for traffic_light, traffic_type in current_traffic_type.items():
                adapter_tl_programs[traffic_light] = TRAFFIC_TYPE_TL_ALGORITHMS[str(int(traffic_type))]
        else:
            adapter_tl_programs = None

        return adapter_tl_programs

    def close_connection(self):
        """
        Close MQTT client connection
        """
        self._mqtt_client.loop_stop()
