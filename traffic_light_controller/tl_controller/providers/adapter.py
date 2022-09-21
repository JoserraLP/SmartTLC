import ast

import paho.mqtt.client as mqtt
from sumo_generators.network.net_graph import NetGraph
from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, TRAFFIC_PREDICTION_TOPIC, TURN_PREDICTION_TOPIC, \
    TRAFFIC_ANALYSIS_TOPIC, DEFAULT_QOS
from sumo_generators.static.constants import NUM_TRAFFIC_TYPES
from tl_controller.providers.utils import retrieve_turns_edges, update_edge_turns_with_probs, is_dict_full
from tl_controller.static.constants import TRAFFIC_TYPE_TL_ALGORITHMS, ERROR_THRESHOLD


class TrafficLightAdapter:
    """
    Traffic Light Adapter class
    """

    def __init__(self, net_graph: NetGraph, id: str, mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT,
                 rows: int = -1, cols: int = -1):
        """
        Traffic Light Adapter initializer.

        :param net_graph: network topology graph
        :type net_graph: NetGraph
        :param id: traffic light junction identifier
        :type id: str
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
        self._traffic_prediction, self._traffic_analysis, self._turn_prediction = None, None, None

        # Define topology rows and cols
        self._rows = rows
        self._cols = cols

        # Define junction connections
        self._turns_per_road = retrieve_turns_edges(net_graph=net_graph, cols=cols)

        # Define identifiers
        self._id = id
        self._adjacent_ids = net_graph.get_adjacent_nodes_by_node(id)
        # Retrieve those ids that are relevant to the adapter (central ones)
        self._all_ids = [junction_id for junction_id in self._adjacent_ids if 'c' in junction_id]
        self._all_ids.append(self._id)

        # Define topics to subscribe to
        self._all_traffic_prediction_topics = [(str(TRAFFIC_PREDICTION_TOPIC + '/' + junction_id), DEFAULT_QOS)
                                               for junction_id in self._all_ids]

        self._all_traffic_analysis_topics = [(str(TRAFFIC_ANALYSIS_TOPIC + '/' + junction_id), DEFAULT_QOS)
                                             for junction_id in self._all_ids]

        # Reset counters
        self.reset_traffic_counters()

        # Create the MQTT client, its callbacks and its connection to the broker
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.message_callback_add(TRAFFIC_PREDICTION_TOPIC + '/#', self.on_message_traffic_prediction)
        self._mqtt_client.message_callback_add(TRAFFIC_ANALYSIS_TOPIC + '/#', self.on_message_traffic_analysis)
        self._mqtt_client.message_callback_add(TURN_PREDICTION_TOPIC + '/' + id, self.on_message_turn_prediction)
        self._mqtt_client.on_connect = self.on_connect
        self._mqtt_client.on_message = self.on_message
        self._mqtt_client.connect(mqtt_url, mqtt_port)
        self._mqtt_client.loop_start()

    def reset_traffic_counters(self):
        self._traffic_prediction = {k: '' for k in self._all_ids}
        self._traffic_analysis = {k: '' for k in self._all_ids}
        self._turn_prediction = None

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
            # Subscribe to the traffic prediction, analysis (adjacent and self) and turn prediction topics
            self._mqtt_client.subscribe(self._all_traffic_prediction_topics)
            self._mqtt_client.subscribe(self._all_traffic_analysis_topics)
            self._mqtt_client.subscribe(TURN_PREDICTION_TOPIC + '/' + self._id)

    def on_message(self, client, userdata, msg):
        """
        Callback called when the client receives a message from to the broker.
        :param client: MQTT client
        :param userdata: MQTT client data
        :param msg: message received from the middleware
        :return: None
        """
        pass

    def on_message_traffic_prediction(self, client, userdata, msg):
        """
        Callback called when the client receives a message from to the traffic prediction topic.
        :param client: MQTT client
        :param userdata: MQTT client data
        :param msg: message received from the middleware
        :return: None
        """
        # Retrieve junction id
        junction_id = str(msg.topic).split('/')[1] if '/' in msg.topic else ''

        # Parse message to dict
        self._traffic_prediction[junction_id] = ast.literal_eval(msg.payload.decode('utf-8'))

    def on_message_traffic_analysis(self, client, userdata, msg):
        """
        Callback called when the client receives a message from to the traffic analysis topic.
        :param client: MQTT client
        :param userdata: MQTT client data
        :param msg: message received from the middleware
        :return: None
        """
        # Retrieve junction id
        junction_id = str(msg.topic).split('/')[1] if '/' in msg.topic else ''

        # Parse message to dict
        self._traffic_analysis[junction_id] = ast.literal_eval(msg.payload.decode('utf-8'))

    def on_message_turn_prediction(self, client, userdata, msg):
        """
        Callback called when the client receives a message from to the turn prediction topic.
        :param client: MQTT client
        :param userdata: MQTT client data
        :param msg: message received from the middleware
        :return: None
        """
        # Parse message to dict
        self._turn_prediction = ast.literal_eval(msg.payload.decode('utf-8'))

        # Retrieve turn prediction -> Update junction connections
        update_edge_turns_with_probs(self._turns_per_road, self._turn_prediction)

    def get_new_tl_program(self) -> dict:
        """
        Retrieve the new traffic light program based on the analyzer, predictor or both.

        :return: new tl program per traffic light
        :rtype: dict
        """
        # TODO with Cristina
        current_traffic_type, adapter_new_tl_program = None, None

        # Calculate adjacent information
        if is_dict_full(self._traffic_analysis) and is_dict_full(self._turn_prediction):
            pass
        
        # If only analyzer is deployed
        if is_dict_full(self._traffic_analysis) and not is_dict_full(self._traffic_prediction):
            current_traffic_type = self._traffic_analysis
        # If only predictor is deployed
        elif is_dict_full(self._traffic_prediction) and not is_dict_full(self._traffic_analysis):
            current_traffic_type = self._traffic_prediction
        # Both analyzer and predictor are deployed
        elif is_dict_full(self._traffic_analysis) and is_dict_full(self._traffic_prediction):
            # Calculate the current traffic type based on both information
            current_traffic_type = self.calculate_current_traffic_type()
            
            # Remove used traffic information -> To check again if there is information available
            self.reset_traffic_counters()

        if current_traffic_type is not None:
            # Retrieve only the self traffic type
            adapter_new_tl_program = TRAFFIC_TYPE_TL_ALGORITHMS[str(int(current_traffic_type))]

        return adapter_new_tl_program

    def calculate_current_traffic_type(self):
        """

        """
        current_traffic_type = None
        # TODO with Cristina
        # Calculate the difference between the traffic types (prediction and analysis)
        error_distance = self._traffic_analysis[self._id] - self._traffic_prediction[self._id]
        # If the distance is less than the threshold
        if abs(error_distance) <= ERROR_THRESHOLD:
            # The analyzer is right, use its value
            current_traffic_type = self._traffic_analysis[self._id]
        # Otherwise calculate the weighted value
        else:
            # 1/3 closest to the analyzer as it is in real time
            new_traffic_type = self._traffic_analysis[self._id] \
                               - int(error_distance / 3)
            if new_traffic_type >= 0 or new_traffic_type <= NUM_TRAFFIC_TYPES:
                # If calculated value is valid, store it
                current_traffic_type = new_traffic_type
        return current_traffic_type

    def close_connection(self):
        """
        Close MQTT client connection
        """
        self._mqtt_client.loop_stop()

    @property
    def adjacent_ids(self):
        """
        Traffic Light Adapter adjacent ids getter

        :return: list of adjacent traffic light ids
        :rtype: list
        """
        return self._adjacent_ids
