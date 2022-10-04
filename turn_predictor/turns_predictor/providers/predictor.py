import ast
import copy

import paho.mqtt.client as mqtt
import pandas as pd
from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, TRAFFIC_INFO_TOPIC, \
    TURN_PREDICTION_TOPIC
from sumo_generators.utils.utils import parse_str_to_valid_schema
from turns_predictor.ml.model_predictor import ModelPredictor
from turns_predictor.static.constants import DEFAULT_NUM_MODELS, MODEL_PARSED_VALUES_FILE, MODEL_BASE_DIR, \
    MODEL_PERFORMANCE_FILE


class TurnPredictor:
    """
    Predictor class that will be subscribed to the middleware for retrieving the traffic info and will publish their
    turn prediction.

    :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
    :type mqtt_url: str
    :param mqtt_port: MQTT middleware broker port. Default to 1883.
    :type mqtt_port: int
    :param num_models: Number of used models. Default to 1.
    :type num_models: int
    :param model_base_dir: directory where the models are stored. Default to '../regression_models/'.
    :type model_base_dir: str
    :param parsed_values_file: directory where the dataset parsed values are stored.
        Default to '../output/parsed_values_dict.json'.
    :type parsed_values_file: str
    :param performance_file: file where the training performances have been stored.
    Default to '../regression_models/ml_performance.json'.
    :type performance_file: str
    """

    def __init__(self, mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT, num_models: int = DEFAULT_NUM_MODELS,
                 model_base_dir: str = MODEL_BASE_DIR, parsed_values_file: str = MODEL_PARSED_VALUES_FILE,
                 performance_file: str = MODEL_PERFORMANCE_FILE) -> None:
        """
        Predictor class initializer.
        """
        # Store the number of models
        self._num_models = num_models

        # Define turn probabilities dict
        self._turn_probabilities = {}

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
            self._mqtt_client.subscribe(TRAFFIC_INFO_TOPIC + '/#')

    def on_message(self, client, userdata, msg) -> None:
        """
        Callback called when the client receives a message from to the broker.

        :param client: MQTT client
        :param userdata: MQTT client data
        :param msg: message received from the middleware
        :return: None
        """
        # Parse to message input dict
        traffic_info = ast.literal_eval(msg.payload.decode('utf-8'))

        # Retrieve junction id
        junction_id = str(msg.topic).split('/')[1] if '/' in msg.topic else ''

        # Check valid value
        if junction_id != '':
            # Predict turn probabilities
            self._turn_probabilities = {junction_id: self.predict_turn_probabilities(traffic_info=traffic_info)}

            # Publish the message
            self._mqtt_client.publish(topic=TURN_PREDICTION_TOPIC + '/' + junction_id,
                                      payload=parse_str_to_valid_schema(self._turn_probabilities))

    def predict_turn_probabilities(self, traffic_info: dict) -> dict:
        """
        Predict the turn probabilities by road given the road and the time information

        :param traffic_info: information related to date and roads
        :type traffic_info: dict
        :return: turn probabilities by road
        :rtype: dict
        """
        # Define the roads
        information_per_road = []

        # Convert the traffic information to dataframe
        traffic_data = pd.DataFrame([list(traffic_info.values())], columns=list(traffic_info.keys()))

        # Information is retrieved from the middleware
        if self._mqtt_client:
            # Remove unused model features
            traffic_data = traffic_data.drop(
                labels=['actual_program', 'waiting_time_veh_e_w', 'waiting_time_veh_n_s', 'turning_vehicles',
                        'day', 'passing_veh_n_s', 'passing_veh_e_w'], axis=1)

        # Parse date info from str to int
        traffic_data['date_day'] = int(traffic_data['date_day'])
        traffic_data['date_year'] = int(traffic_data['date_year'])
        traffic_data['date_month'] = int(traffic_data['date_month'])

        # Create a list with the information per road
        for road in traffic_data['roads'][0]:
            information_per_road.append({
                'road': road,
                'date_year': traffic_data['date_year'][0],
                'date_month': traffic_data['date_month'][0],
                'date_day': traffic_data['date_day'][0],
                'hour': traffic_data['hour'][0]
            })

        # Parse dict list to dataframe
        information_per_road = pd.DataFrame.from_dict(information_per_road)

        # Store an auxiliary variable for training data as it is parsed when performing the prediction
        training_information_per_road = copy.copy(information_per_road)

        # Retrieve predictions
        turn_predictions = self._model_predictor.predict(training_information_per_road, num_models=self._num_models)[0]

        # Define a dict for the predicted values per road
        turn_predictions_per_road = dict()

        # Iterate over the roads and store the predictions
        for index, row in information_per_road.iterrows():
            turn_predictions_per_road[row['road']] = turn_predictions[index].tolist()

        self._turn_probabilities = turn_predictions_per_road

        return self._turn_probabilities

    @property
    def turn_probabilities(self):
        """
        Turn Predictor probabilities getter

        :return: turn probabilities
        """
        return self._turn_probabilities
