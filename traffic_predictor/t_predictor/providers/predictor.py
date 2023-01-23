import ast

import paho.mqtt.client as mqtt
import pandas as pd

from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, TRAFFIC_PREDICTION_TOPIC, DEFAULT_TOPICS, DEFAULT_QOS
from sumo_generators.utils.utils import parse_to_valid_schema
from t_predictor.ml.model_predictor import ModelPredictor
from t_predictor.static.constants import DEFAULT_NUM_MODELS, MODEL_PARSED_VALUES_FILE, COLUMNS_PREDICTOR


class TrafficPredictor:
    """
    Predictor class that will be subscribed to the middleware for retrieving the traffic info and will publish their
    traffic type prediction.

    :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
    :type mqtt_url: str
    :param mqtt_port: MQTT middleware broker port. Default to 1883.
    :type mqtt_port: int
    :param num_models: Number of used models. Default to 1.
    :type num_models: int
    :param topics: topics to subscribe to
    :type topics: list
    """

    def __init__(self, model_base_dir: str, performance_file: str, mqtt_url: str = MQTT_URL,
                 mqtt_port: int = MQTT_PORT, num_models: int = DEFAULT_NUM_MODELS,
                 parsed_values_file: str = MODEL_PARSED_VALUES_FILE, topics: list = DEFAULT_TOPICS) -> None:
        """
        Predictor class initializer.
        """
        # Retrieve topics
        self._topics = [(topic, DEFAULT_QOS) for topic in topics]

        # Store the number of models
        self._num_models = num_models

        # Define traffic type
        self._traffic_type = 0

        # Create model predictor
        self._model_predictor = ModelPredictor(model_base_dir=model_base_dir, parsed_values_file=parsed_values_file)

        # Load all the models
        self._model_predictor.load_best_models(num_models=self._num_models, performance_file=performance_file)

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

    def on_connect(self, client, userdata, flags, rc) -> None:
        """
        Callback called when the client connects to the broker.

        :param client: MQTT client
        :param userdata: MQTT client data
        :param flags: MQTT connection flags
        :param rc: MQTT connection response code
        :return: None
        """
        # If connected successfully
        if rc == 0:
            # Subscribe to the traffic info topic from all traffic lights -> Append #
            self._mqtt_client.subscribe(self._topics)

    def on_message(self, client, userdata, msg) -> None:
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
            # Create payload with the lane information and the traffic type analysis
            payload = {
                lane_info['lane']: self.predict_traffic_type(lane_info=lane_info)}
            # Publish the payload
            self._mqtt_client.publish(topic=TRAFFIC_PREDICTION_TOPIC + '/' + lane_info['tl_id'],
                                      payload=parse_to_valid_schema(payload))

    def predict_traffic_type(self, lane_info: dict) -> int:
        """
        Predict the traffic type for a given junction at a given instant

        :param lane_info: information related to a given road and date
        :type lane_info: dict
        :return: traffic type
        :rtype: int
        """
        # Convert the traffic information to dataframe by selecting valid columns
        traffic_data = pd.DataFrame.from_dict(lane_info, orient='index', columns=COLUMNS_PREDICTOR)

        # Add road column
        traffic_data = traffic_data.reset_index(names=['road'])

        # In the future as the time patterns will be road-specific, use also the 'road' column field
        # Copy the value if not there is an error
        traffic_data_no_road = traffic_data.iloc[:, 1:].copy()

        # Predict the traffic type
        self._traffic_type = self._model_predictor.predict(traffic_data_no_road, num_models=self._num_models)[0]

        # Return the prediction
        return self._traffic_type

    @property
    def traffic_type(self) -> int:
        """
        Analyzer traffic type

        :return: traffic type id
        :rtype: ind
        """
        return self._traffic_type
