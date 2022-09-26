import ast

import paho.mqtt.client as mqtt
from sumo_generators.network.net_graph import NetGraph
from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, DEFAULT_QOS, TRAFFIC_INFO_TOPIC
from tl_controller.providers.utils import retrieve_turns_edges
from tl_controller.static.constants import TRAFFIC_TYPE_TL_ALGORITHMS


class TrafficLightAdapter:
    """
    Traffic Light Adapter class
    """

    def __init__(self, net_graph: NetGraph, id: str, mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT,
                 rows: int = -1, cols: int = -1, local: bool = False):
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
        :param local: flag to execute locally the component. It will not connect to the middleware.
        :type local: bool
        """
        # Store adjacent traffic info
        self._adjacent_traffic_info = None

        # Define topology rows and cols
        self._rows, self._cols = rows, cols

        # Store the local flag
        self._local = local

        # Define junction connections
        self._turns_per_road = retrieve_turns_edges(net_graph=net_graph, cols=cols)

        # Define identifiers
        self._id = id
        self._adjacent_ids = net_graph.get_adjacent_nodes_by_node(id)

        # Retrieve those ids that are relevant to the adapter (central ones)
        self._all_ids = [junction_id for junction_id in self._adjacent_ids if 'c' in junction_id]

        # Define topics to subscribe to
        self._all_traffic_info_topics = [(str(TRAFFIC_INFO_TOPIC + '/' + junction_id), DEFAULT_QOS)
                                         for junction_id in self._all_ids]

        # Reset counters
        self.reset_traffic_counters()

        if self._local:
            self._mqtt_client = None
        else:
            # Create the MQTT client, its callbacks and its connection to the broker
            self._mqtt_client = mqtt.Client()
            self._mqtt_client.message_callback_add(TRAFFIC_INFO_TOPIC + '/#', self.on_message_traffic_analysis)
            self._mqtt_client.on_connect = self.on_connect
            self._mqtt_client.on_message = self.on_message
            self._mqtt_client.connect(mqtt_url, mqtt_port)
            self._mqtt_client.loop_start()

    def reset_traffic_counters(self) -> None:
        """
        Reset adjacent traffic info counters

        :return: None
        """
        self._adjacent_traffic_info = {k: '' for k in self._all_ids}

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
            # Subscribe to the traffic information of adjacent neighbors
            self._mqtt_client.subscribe(self._all_traffic_info_topics)

    def on_message(self, client, userdata, msg):
        """
        Callback called when the client receives a message from to the broker.
        :param client: MQTT client
        :param userdata: MQTT client data
        :param msg: message received from the middleware
        :return: None
        """
        pass

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
        self._adjacent_traffic_info[junction_id] = ast.literal_eval(msg.payload.decode('utf-8'))

    def get_new_tl_program(self, traffic_analysis: int) -> int:
        """
        Retrieve the new traffic light program based on the analyzer, predictor or both.

        :param traffic_analysis: traffic analyzer value
        :type traffic_analysis: int

        :return: new tl program
        :rtype: int
        """
        current_traffic_type, adapter_new_tl_program = None, None

        # TODO define the adaptation process with Cristina, now it is only based on the traffic analysis

        # If only analyzer is deployed
        if traffic_analysis != -1:
            current_traffic_type = traffic_analysis

        if current_traffic_type is not None:
            # Retrieve only the self traffic type
            adapter_new_tl_program = TRAFFIC_TYPE_TL_ALGORITHMS[str(int(current_traffic_type))]

        return adapter_new_tl_program

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
