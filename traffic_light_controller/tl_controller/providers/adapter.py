import ast

import paho.mqtt.client as mqtt
from sumo_generators.network.net_graph import NetGraph
from sumo_generators.static.constants import NUM_TRAFFIC_TYPES, TRAFFIC_TYPE_RELATION
from tl_controller.providers.utils import get_adjacent_junctions_probs, get_new_traffic_type_by_direction, \
    retrieve_turns_edges, update_edge_turns_with_probs
from tl_controller.static.constants import TRAFFIC_TYPE_TL_ALGORITHMS, ERROR_THRESHOLD, MQTT_URL, MQTT_PORT, \
    TRAFFIC_PREDICTION_TOPIC, TURN_PREDICTION_TOPIC, ANALYSIS_TOPIC


class TrafficLightAdapter:
    """
    Traffic Light Adapter class
    """

    def __init__(self, net_graph: NetGraph, traffic_prediction=None, traffic_analysis=None, turn_prediction=None,
                 mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT, rows: int = -1, cols: int = -1):
        """
        TraCISimulator initializer.

        :param net_graph: network topology graph
        :type net_graph: NetGraph
        :param traffic_prediction: traffic prediction dict. Default is None.
        :type traffic_prediction: dict
        :param traffic_analysis: traffic analysis dict. Default is None.
        :type traffic_analysis: dict
        :param turn_prediction: turn prediction dict. Default is None.
        :type turn_prediction: dict
        :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
        :type mqtt_url: str
        :param mqtt_port: MQTT middleware broker port. Default to 1883.
        :type mqtt_port: int
        :param rows: topology rows. Default to -1.
        :type rows: int
        :param cols: topology cols. Default to -1.
        :type cols: int
        """
        # Store traffic prediction, traffic analysis and turn prediction
        self._traffic_prediction = traffic_prediction
        self._traffic_analysis = traffic_analysis
        self._turn_prediction = turn_prediction

        # Define topology rows and cols
        self._rows = rows
        self._cols = cols

        # Define junction connections
        self._turns_per_road = retrieve_turns_edges(net_graph=net_graph, cols=cols)

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
            # Subscribe to the traffic prediction, analysis and turn prediction topics
            self._mqtt_client.subscribe(TRAFFIC_PREDICTION_TOPIC)
            self._mqtt_client.subscribe(ANALYSIS_TOPIC)
            self._mqtt_client.subscribe(TURN_PREDICTION_TOPIC)

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
        if msg.topic == TRAFFIC_PREDICTION_TOPIC:
            # Retrieve predicted traffic type
            self._traffic_prediction = traffic_info
        if msg.topic == ANALYSIS_TOPIC:
            # Retrieve analyzed traffic type
            self._traffic_analysis = traffic_info
        if msg.topic == TURN_PREDICTION_TOPIC:
            self._turn_prediction = traffic_info
            # Retrieve turn prediction -> Update junction connections
            update_edge_turns_with_probs(self._turns_per_road, traffic_info)

    def get_new_tl_program(self) -> dict:
        """
        Retrieve the new traffic light program based on the analyzer, predictor or both.

        :return: new tl program per traffic light
        :rtype: dict
        """
        current_traffic_type = None

        if self._traffic_analysis and self._turn_prediction:
            current_traffic_type = {}
            current_traffic_analysis = {}
            # TODO process the information to propagate the neighbor information
            for junction, traffic_type in self._traffic_analysis.items():
                adjacent_junction_ns, adjacent_junction_ew = get_adjacent_junctions_probs(
                    turns_per_road=self._turns_per_road,
                    junction=junction)

                # NS
                new_traffic_type_ns = get_new_traffic_type_by_direction(adjacent_junction_probs=adjacent_junction_ns,
                                                                        traffic_analysis=self._traffic_analysis,
                                                                        direction='ns')

                # EW
                new_traffic_type_ew = get_new_traffic_type_by_direction(adjacent_junction_probs=adjacent_junction_ew,
                                                                        traffic_analysis=self._traffic_analysis,
                                                                        direction='ew')
                current_traffic_type[junction] = (new_traffic_type_ns, new_traffic_type_ew)


                found = False
                for k, v in TRAFFIC_TYPE_RELATION.items():
                    if v == (new_traffic_type_ns, new_traffic_type_ew):
                        found = True
                        break

                # TODO there are cases where the traffic is "Very Low" y "Medium", and as they are not represented yet,
                # it fails, in order to fix it. Define more traffic types
                if found:
                    current_traffic_type[junction] = [k for k, v in TRAFFIC_TYPE_RELATION.items()
                                                      if v == (new_traffic_type_ns, new_traffic_type_ew)][0]

                current_traffic_analysis[junction] = TRAFFIC_TYPE_RELATION[traffic_type]

        # If only analyzer is deployed
        if self._traffic_analysis and not self._traffic_prediction:
            current_traffic_type = self._traffic_analysis
        # If only predictor is deployed
        elif self._traffic_prediction and not self._traffic_analysis:
            current_traffic_type = self._traffic_prediction
        elif self._traffic_analysis and self._traffic_prediction:
            current_traffic_type = dict()
            # If both analyzer and predictor are deployed
            if self._traffic_analysis and self._traffic_prediction:
                # It is chosen the traffic_analysis but can be used both as they have the same information
                for traffic_light in self._traffic_analysis.keys():
                    # update this
                    self.calculate_actual_traffic_type(current_traffic_type=current_traffic_type,
                                                       traffic_light=traffic_light)

                # Store the difference between prediction and analysis
                # self._adapt_items.append(abs(self._traffic_prediction - self._traffic_analysis))

                # Remove used traffic information -> To check again if there is information available
                self._traffic_analysis = None
                self._traffic_prediction = None
                self._turn_prediction = None

        adapter_tl_programs = dict()

        if current_traffic_type is not None:
            # If the traffic type exists get the new traffic light program per traffic light
            for traffic_light, traffic_type in current_traffic_type.items():
                adapter_tl_programs[traffic_light] = TRAFFIC_TYPE_TL_ALGORITHMS[str(int(traffic_type))]
        else:
            adapter_tl_programs = None

        return adapter_tl_programs

    def calculate_actual_traffic_type(self, current_traffic_type, traffic_light):
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
            new_traffic_type = self._traffic_analysis[traffic_light] \
                               - int(error_distance / 3)
            if new_traffic_type >= 0 or new_traffic_type <= NUM_TRAFFIC_TYPES:
                # If calculated value is valid, store it
                current_traffic_type[traffic_light] = new_traffic_type

    def close_connection(self):
        """
        Close MQTT client connection
        """
        self._mqtt_client.loop_stop()
