from tl_controller.static.constants import TRAFFIC_TYPE_TL_ALGORITHMS, ERROR_THRESHOLD, MQTT_URL, MQTT_PORT, \
    PREDICTION_TOPIC, ANALYSIS_TOPIC
import paho.mqtt.client as mqtt
import ast


class TrafficLightAdapter:

    def __init__(self, traffic_prediction=None, traffic_analysis=None, mqtt_url: str = MQTT_URL,
                 mqtt_port: int = MQTT_PORT):
        self._traffic_prediction = traffic_prediction
        self._traffic_analysis = traffic_analysis

        # Create the MQTT client, its callbacks and its connection to the broker
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self.on_connect
        self._mqtt_client.on_message = self.on_message
        self._mqtt_client.connect(mqtt_url, mqtt_port)
        self._mqtt_client.loop_start()

    def on_connect(self, client, userdata, flags, rc):  # The callback for when the client connects to the broker
        if rc == 0:  # Connection established
            # Subscribe to the traffic prediction and analysis topic
            self._mqtt_client.subscribe(PREDICTION_TOPIC)
            self._mqtt_client.subscribe(ANALYSIS_TOPIC)

    def on_message(self, client, userdata,
                   msg):  # The callback for when a PUBLISH message is received from the server.
        # Parse message to dict
        traffic_info = ast.literal_eval(msg.payload.decode('utf-8'))

        # Check the topic it comes from
        if msg.topic == PREDICTION_TOPIC:
            # Retrieve predicted traffic type
            traffic_type = int(traffic_info['traffic_prediction'])
            self._traffic_prediction = traffic_type
        if msg.topic == ANALYSIS_TOPIC:
            # Retrieve analyzed traffic type
            traffic_type = int(traffic_info['traffic_analysis'])
            self._traffic_analysis = traffic_type

    def get_new_tl_program(self):
        current_traffic_type = None
        if self._traffic_analysis and not self._traffic_prediction:
            current_traffic_type = self._traffic_analysis
        elif self._traffic_prediction and not self._traffic_analysis:
            current_traffic_type = self._traffic_prediction
        else:
            # Calculate the difference between the traffic types
            if self._traffic_analysis and self._traffic_prediction:
                error_distance = self._traffic_analysis - self._traffic_prediction
                if abs(error_distance) <= ERROR_THRESHOLD:
                    # The analyzer is right, use its value
                    current_traffic_type = self._traffic_analysis
                else:
                    # The analyzer might be wrong, get a "neutral" value -> 1/3 closest to the analyzer as it is in
                    # real time
                    new_traffic_type = self._traffic_analysis - int(error_distance / 3)
                    if new_traffic_type >= 0 or new_traffic_type <= 11:
                        current_traffic_type = new_traffic_type
        if current_traffic_type is not None:
            new_tl_program = TRAFFIC_TYPE_TL_ALGORITHMS[str(current_traffic_type)]
        else:
            new_tl_program = None

        return new_tl_program

    def close_connection(self):
        self._mqtt_client.loop_stop()
