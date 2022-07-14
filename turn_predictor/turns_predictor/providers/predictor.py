import ast

import paho.mqtt.client as mqtt
import pandas as pd
from turns_predictor.ml.model_predictor import ModelPredictor
from turns_predictor.static.constants import MQTT_URL, MQTT_PORT, DEFAULT_NUM_MODELS, PREDICTION_TOPIC, \
    TRAFFIC_INFO_TOPIC


class Predictor:
    """
    Predictor class that will be subscribed to the middleware for retrieving the traffic info and will publish their
    turn prediction.
    """

    def __init__(self, mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT,
                 num_models: int = DEFAULT_NUM_MODELS) -> None:
        """
        Predictor class initializer.

        :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
        :type mqtt_url: str
        :param mqtt_port: MQTT middleware broker port. Default to 1883.
        :type mqtt_port: int
        :param num_models: Number of used models. Default to 1.
        :type num_models: int
        """
        # Store the number of models
        self._num_models = num_models

        # Create model predictor
        self._model_predictor = ModelPredictor()

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

        # Define used variables
        processed_data = []
        roads = set()

        # Iterate over the traffic lights
        for traffic_light_info in traffic_info:
            traffic_light_id = traffic_light_info['tl_id']

            # Remove summary information
            if traffic_light_info['tl_id'] != 'summary':
                traffic_light_info.pop("tl_id", None)
                # Convert to dataframe
                traffic_data = pd.DataFrame([list(traffic_light_info.values())],
                                            columns=list(traffic_light_info.keys()))

                # Remove unused model features
                traffic_data = traffic_data.drop(
                    labels=['tl_program', 'waiting_time_veh_e_w', 'waiting_time_veh_n_s', 'turning_vehicles',
                            'turning_vehicles', 'day', 'passing_veh_n_s', 'passing_veh_e_w'], axis=1)

                # Parse date info from str to int
                traffic_data['date_day'] = int(traffic_data['date_day'])
                traffic_data['date_year'] = int(traffic_data['date_year'])
                traffic_data['date_month'] = int(traffic_data['date_month'])

                # Create a list with the information per road
                for road in traffic_data['roads'][0]:
                    processed_data.append({
                        'road': road,
                        'date_year': traffic_data['date_year'][0],
                        'date_month': traffic_data['date_month'][0],
                        'date_day': traffic_data['date_day'][0],
                        'hour': traffic_data['hour'][0]
                    })
                    roads.add(road)

        # Parse dict list to dataframe
        processed_data = pd.DataFrame.from_dict(processed_data)

        # Retrieve predictions
        turn_predictions = self._model_predictor.predict(processed_data, num_models=self._num_models)[0]

        # Define a dict for the predicted values per road
        turn_predictions_per_road = dict()
        # iterate over the roads and store the predictions
        for index, road in enumerate(roads):
            turn_predictions_per_road[road] = turn_predictions[index].tolist()

        # Publish the message
        self._mqtt_client.publish(topic=PREDICTION_TOPIC, payload=str(turn_predictions_per_road).replace('\'', '"')
                                  .replace(' ', ''))
