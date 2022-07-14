import ast

import paho.mqtt.client as mqtt
import pandas as pd

from t_predictor.ml.model_predictor import ModelPredictor
from t_predictor.static.constants import MQTT_URL, MQTT_PORT, DEFAULT_NUM_MODELS, PREDICTION_TOPIC, TRAFFIC_INFO_TOPIC


class Predictor:
    """
    Predictor class that will be subscribed to the middleware for retrieving the traffic info and will publish their
    traffic type prediction.
    """

    def __init__(self, date: bool = True, mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT,
                 num_models: int = DEFAULT_NUM_MODELS) -> None:
        """
        Predictor class initializer.

        :param date: if True train models based on date only, otherwise with contextual information too.
            Default to True.
        :type date: bool
        :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
        :type mqtt_url: str
        :param mqtt_port: MQTT middleware broker port. Default to 1883.
        :type mqtt_port: int
        :param num_models: Number of used models. Default to 1.
        :type num_models: int
        """
        # Store the number of models
        self._num_models = num_models

        # Store if models are trained in date only
        self._date = date

        # Create model predictor
        self._model_predictor = ModelPredictor(date)

        # Create the MQTT client, its callbacks and its connection to the broker
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self.on_connect
        self._mqtt_client.on_message = self.on_message
        self._mqtt_client.connect(mqtt_url, mqtt_port)
        self._mqtt_client.loop_forever()

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
            # Subscribe to the traffic info topic
            self._mqtt_client.subscribe(TRAFFIC_INFO_TOPIC)

            # Load all the models when connecting to the middleware
            self._model_predictor.load_best_models(num_models=self._num_models)

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

        # Define analysis variable
        traffic_predictions = dict()

        # Iterate over the traffic lights
        for traffic_light_info in traffic_info:
            traffic_light_id = traffic_light_info['tl_id']

            # Remove summary information
            if traffic_light_info['tl_id'] != 'summary':
                traffic_light_info.pop("tl_id", None)
                # Convert to dataframe
                traffic_data = pd.DataFrame([list(traffic_light_info.values())], columns=list(traffic_light_info.keys()))

                # Remove unused model features
                traffic_data = traffic_data.drop(
                    labels=['tl_program', 'waiting_time_veh_e_w', 'waiting_time_veh_n_s', 'turning_vehicles', 'roads'], axis=1)

                # Remove the number of vehicles passing features
                if self._date:
                    traffic_data = traffic_data.drop(labels=['passing_veh_e_w', 'passing_veh_n_s'], axis=1)
                else:
                    # Otherwise multiply by 5 because it fits the best to the actual traffic
                    traffic_data['passing_veh_e_w'] = traffic_data['passing_veh_e_w']*5
                    traffic_data['passing_veh_n_s'] = traffic_data['passing_veh_n_s']*5

                # Set the prediction into the published message
                traffic_predictions[traffic_light_id] = self._model_predictor.predict(traffic_data,
                                                                                      num_models=self._num_models)[0]

        # Publish the message
        self._mqtt_client.publish(topic=PREDICTION_TOPIC, payload=str(traffic_predictions).replace('\'', '"')
                                  .replace(' ', ''))
