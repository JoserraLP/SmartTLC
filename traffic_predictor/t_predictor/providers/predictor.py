import ast

import paho.mqtt.client as mqtt
import pandas as pd
from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, TRAFFIC_PREDICTION_TOPIC, TRAFFIC_INFO_TOPIC, \
    DEFAULT_TEMPORAL_WINDOW
from sumo_generators.utils.utils import parse_str_to_valid_schema
from t_predictor.ml.model_predictor import ModelPredictor
from t_predictor.static.constants import DEFAULT_NUM_MODELS, MODEL_PARSED_VALUES_FILE


def calculate_proportion_value(temporal_window: float) -> float:
    """
    Calculates the value that will be used to multiply the actual number of vehicles in order to fit the trained values

    :param temporal_window: retrieval information
    :type temporal_window: float
    :return: proportion value
    :rtype: float
    """
    # TODO calculate with a more accurate formula
    # Now this formula outputs a value of 5 for a temporal window of 5 minutes, that is the used on the examples and
    # and the value that better fits
    # Trained with a temporal window of 30 minutes
    return (30 / temporal_window) - 1 if temporal_window != 30 else 1


class TrafficPredictor:
    """
    Predictor class that will be subscribed to the middleware for retrieving the traffic info and will publish their
    traffic type prediction.

    :param date: if True train models based on date only, otherwise with contextual information too.
        Default to True.
    :type date: bool
    :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
    :type mqtt_url: str
    :param mqtt_port: MQTT middleware broker port. Default to 1883.
    :type mqtt_port: int
    :param num_models: Number of used models. Default to 1.
    :type num_models: int
    :param temporal_window: monitoring temporal window. Default to 5.
    :type temporal_window: float
    """

    def __init__(self, model_base_dir: str, performance_file: str, date: bool = True, mqtt_url: str = MQTT_URL,
                 mqtt_port: int = MQTT_PORT, num_models: int = DEFAULT_NUM_MODELS,
                 temporal_window: float = DEFAULT_TEMPORAL_WINDOW, parsed_values_file: str = MODEL_PARSED_VALUES_FILE) \
            -> None:
        """
        Predictor class initializer.
        """
        # Store the number of models
        self._num_models = num_models

        # Store if models are trained in date only
        self._date = date

        # Create model predictor
        self._model_predictor = ModelPredictor(model_base_dir=model_base_dir, parsed_values_file=parsed_values_file,
                                               date=date)

        # Load all the models
        self._model_predictor.load_best_models(num_models=self._num_models, performance_file=performance_file)

        # Retrieve proportion value
        self._window_proportion = calculate_proportion_value(temporal_window=temporal_window)

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
            # Predict traffic type
            predicted_traffic_type = {junction_id: self.predict_traffic_type(traffic_info=traffic_info)}
            
            # Publish the message
            self._mqtt_client.publish(topic=TRAFFIC_PREDICTION_TOPIC + '/' + junction_id,
                                      payload=parse_str_to_valid_schema(predicted_traffic_type))

    def predict_traffic_type(self, traffic_info: dict) -> int:
        """
        Predict the traffic type for a given junction at a given instant

        :param traffic_info: information related to date and roads
        :type traffic_info: dict
        :return: traffic type
        :rtype: int
        """
        # Convert the traffic information to dataframe
        traffic_data = pd.DataFrame([list(traffic_info.values())], columns=list(traffic_info.keys()))

        # Remove unused model features
        traffic_data = traffic_data.drop(
            labels=['actual_program', 'waiting_time_veh_e_w', 'waiting_time_veh_n_s', 'turning_vehicles', 'roads'],
            axis=1)

        # Remove the number of vehicles passing features
        if self._date:
            traffic_data = traffic_data.drop(labels=['passing_veh_e_w', 'passing_veh_n_s'], axis=1)
        else:
            # Otherwise multiply by proportion value as there are number of vehicles used to predict
            traffic_data['passing_veh_e_w'] = traffic_data['passing_veh_e_w'] * self._window_proportion
            traffic_data['passing_veh_n_s'] = traffic_data['passing_veh_n_s'] * self._window_proportion

        # Return the prediction
        return self._model_predictor.predict(traffic_data, num_models=self._num_models)[0]
