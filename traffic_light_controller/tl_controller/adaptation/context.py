import ast

import paho.mqtt.client as mqtt
from sumo_generators.network.net_graph import NetGraph
from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, DEFAULT_QOS, TRAFFIC_INFO_TOPIC, \
    TRAFFIC_ANALYSIS_TOPIC, TURN_PREDICTION_TOPIC, TRAFFIC_PREDICTION_TOPIC
from sumo_generators.utils.utils import parse_str_to_valid_schema
from t_analyzer.providers.analyzer import TrafficAnalyzer
from t_predictor.providers.predictor import TrafficPredictor
from tl_controller.adaptation.strategy import AdaptationStrategy
from tl_controller.providers.utils import retrieve_turns_edges, process_payload
from turns_predictor.providers.predictor import TurnPredictor


class TrafficLightAdapter:
    """
    The Traffic Light Adapter defines the interface of interest and stores other relevant information
    """

    def __init__(self, adaptation_strategy: AdaptationStrategy, net_graph: NetGraph, traci, id: str,
                 mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT, rows: int = -1,
                 cols: int = -1, local: bool = False) -> None:
        """
        Traffic Light Adapter initializer.

        :param adaptation_strategy: adaptation concrete strategy
        :type adaptation_strategy: AdaptationStrategy
        :param net_graph: network topology graph
        :type net_graph: NetGraph
        :param traci: TraCI instance
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
        # Store the adaptation strategy
        self._adaptation_strategy = adaptation_strategy

        # Store parameter values
        self._rows, self._cols, self._local, self._id, self._traci = rows, cols, local, id, traci

        # Initialize traffic analyzer, turn predictor and traffic predictor to None
        self._traffic_analyzer, self._turn_predictor, self._traffic_predictor = None, None, None

        # Initialize adjacent and self traffic info dict
        self._adjacent_traffic_info, self._traffic_info, self._publish_info = {}, {}, {}

        # Retrieve connected roads
        self._roads = list(set([self._traci.lane.getEdgeID(lane) for lane
                                in set(self._traci.trafficlight.getControlledLanes(id))]))

        # Define traffic light information schema
        self._traffic_light_info = {
            'passing_veh_n_s': 0, 'passing_veh_e_w': 0, 'waiting_time_veh_n_s': 0, 'waiting_time_veh_e_w': 0,
            'vehicles_passed': set(), 'turning_vehicles': {'forward': 0, 'right': 0, 'left': 0,
                                                           'vehicles_passed': set()},
            'roads': self._roads, 'actual_program': self._traci.trafficlight.getProgram(id)
        }

        # Define junction connections
        self._turns_per_road = retrieve_turns_edges(net_graph=net_graph, cols=cols)

        # Define identifiers
        self._adjacent_ids = net_graph.get_adjacent_nodes_by_node(id)

        # Retrieve those ids that are relevant to the adapter (central ones)
        self._all_ids = [junction_id for junction_id in self._adjacent_ids if 'c' in junction_id]

        # Define topics to subscribe to
        self._all_traffic_info_topics = [(str(TRAFFIC_INFO_TOPIC + '/' + junction_id), DEFAULT_QOS)
                                         for junction_id in self._all_ids]

        # Get the waiting time per lane when the traffic light is created
        self._prev_waiting_time = {lane: traci.lane.getWaitingTime(lane) for lane in
                                   list(dict.fromkeys(traci.trafficlight.getControlledLanes(id)))}

        # Store those detectors related to the traffic light
        self._traffic_light_detectors = [detector for detector in self._traci.inductionloop.getIDList()
                                         if traci.inductionloop.getLaneID(detector).split('_')[1] == id]

        # Reset counters
        self.reset_traffic_counters()

        if self._local:
            self._mqtt_client = None
        else:
            # Create the MQTT client, its callbacks and its connection to the broker
            self._mqtt_client = mqtt.Client()
            self._mqtt_client.on_connect = self.on_connect
            self._mqtt_client.on_message = self.on_message
            self._mqtt_client.connect(mqtt_url, mqtt_port)
            self._mqtt_client.loop_start()

    """ TRAFFIC LIGHT UTILS """

    def update_tl_program(self) -> str:
        """
        Traffic Light Adapter delegates on the adaptation strategy the retrieval of the new traffic light
        """
        # Gather all the traffic light information (self and adjacent)
        all_traffic_info = dict(self._traffic_light_info)

        if self._adjacent_traffic_info:
            all_traffic_info.update(self._adjacent_traffic_info)

        # Get new traffic light algorithm based on the adaptation strategy
        new_tl_program = self._adaptation_strategy.get_new_tl_program(all_traffic_info)

        # Check if the new program is valid and it is not the same as the actual one
        if new_tl_program and new_tl_program != self._traffic_light_info['actual_program']:
            # Update new program
            self._traci.trafficlight.setProgram(self._id, new_tl_program)

    """ VEHICLE UTILS """

    def increase_turning_vehicles(self, turn: str) -> None:
        """
        Increase the number of turning vehicles by 1 on the given turn

        :param turn: turn direction
        :type turn: str
        :return: None
        """
        self._traffic_light_info['turning_vehicles'][turn] += 1

    def append_turning_vehicle(self, vehicle_id: str) -> None:
        """
        Append a vehicle to the list of turning vehicles of the traffic light

        :param vehicle_id: vehicle identifier
        :type vehicle_id: str
        :return: None
        """
        self._traffic_light_info['turning_vehicles']['vehicles_passed'].add(vehicle_id)

    def is_vehicle_turning_counted(self, vehicle_id: str) -> None:
        """
        Check if a turning vehicles has been counted previously

        :param vehicle_id: vehicle identifier
        :type vehicle_id: str
        :return: True if it is counted, False otherwise
        :rtype: bool
        """
        return vehicle_id in self._traffic_light_info['turning_vehicles']['vehicles_passed']

    def count_passing_vehicles(self) -> None:
        """
        Update the counters of vehicles passing on both directions (NS and EW), appending them to the list

        :return: None
        """
        # Initialize dictionary
        num_passing_vehicles = {'north': 0, 'east': 0, 'south': 0, 'west': 0}

        # Iterate over the traffic light detectors
        for detector in self._traffic_light_detectors:

            # Get detector direction
            detector_direction = detector.split('_')[0]

            # Get the current passing vehicles
            cur_veh = set(self._traci.inductionloop.getLastStepVehicleIDs(detector))

            # Calculate the difference between the sets
            not_counted_veh = cur_veh - self._traffic_light_info['vehicles_passed']

            # If there are no counted vehicles
            if not_counted_veh:
                # Append the not counted vehicles
                self._traffic_light_info['vehicles_passed'].update(not_counted_veh)

                # Add the number of not counted vehicles
                num_passing_vehicles[detector_direction] += len(not_counted_veh)

        # Update number of vehicles passing
        self._traffic_light_info['passing_veh_n_s'] += num_passing_vehicles['north'] + num_passing_vehicles['south']
        self._traffic_light_info['passing_veh_e_w'] += num_passing_vehicles['east'] + num_passing_vehicles['west']

# TODO make a wrapper to validate the information passed to the analyzer and predictors, based on the adaptation strategy

    def retrieve_edges_vehicles(self) -> dict:
        """
        Retrieve the vehicles that are on each one of the possible directions (North, East, South, West)

        :return: vehicles per direction
        :rtype: dict
        """
        # Dict with vehicles per direction
        vehicles_per_direction = {'north': [], 'east': [], 'south': [], 'west': []}

        # Iterate over the detectors
        for detector in self._traffic_light_detectors:
            # Get the current passing vehicles
            cur_veh = set(self._traci.inductionloop.getLastStepVehicleIDs(detector))

            # If there are vehicles
            if cur_veh:

                # North
                if 'north' in detector:
                    vehicles_per_direction['north'] += list(cur_veh)
                # East
                elif 'east' in detector:
                    vehicles_per_direction['east'] += list(cur_veh)
                # South
                elif 'south' in detector:
                    vehicles_per_direction['south'] += list(cur_veh)
                # West
                elif 'west' in detector:
                    vehicles_per_direction['west'] += list(cur_veh)

        return vehicles_per_direction

    def calculate_waiting_time_per_lane(self, cols: int) -> None:
        """
        Calculate and update the waiting time per lane.

        :param cols: number of topology columns
        :type cols: int
        :return: None
        """
        # Calculate current waiting time
        current_waiting_time = {lane: self._traci.lane.getWaitingTime(lane) for lane in
                                list(dict.fromkeys(self._traci.trafficlight.getControlledLanes(self._id)))}

        # Iterate over the lanes
        for lane, waiting_time in current_waiting_time.items():
            # If the information is valid (there are no more vehicles waiting)
            if self._prev_waiting_time[lane] > waiting_time:
                # Retrieve the origin and destination junctions
                origin, destination, _ = lane.split('_')

                # Append waiting time to NS on outer edges
                if ('n' in destination or ('s' in origin and 'c' in destination)) or \
                        ('s' in destination or ('n' in origin and 'c' in destination)):
                    self._traffic_light_info['waiting_time_veh_n_s'] += self._prev_waiting_time[lane]
                # Append waiting time to EW on outer edges
                if ('e' in destination or ('w' in origin and 'c' in destination)) or \
                        ('w' in destination or ('e' in origin and 'c' in destination)):
                    self._traffic_light_info['waiting_time_veh_e_w'] += self._prev_waiting_time[lane]
                # Inner edges
                if 'c' in origin and 'c' in destination:
                    # Get the junction identifiers
                    prev_tl_id, next_tl_id = int(origin[1:]), int(destination[1:])

                    # North-South - Append waiting time to NS
                    if prev_tl_id + cols == next_tl_id or prev_tl_id - cols == next_tl_id:
                        self._traffic_light_info['waiting_time_veh_n_s'] += self._prev_waiting_time[lane]
                    # East-West - Append waiting time to EW
                    elif prev_tl_id + 1 == next_tl_id or prev_tl_id - 1 == next_tl_id:
                        self._traffic_light_info['waiting_time_veh_e_w'] += self._prev_waiting_time[lane]

        # Update the previous waiting time to the current waiting time
        self._prev_waiting_time = current_waiting_time

    def remove_passing_vehicles(self) -> None:
        """
        Remove those vehicles that have passed on a edge close to the junction but it is not anymore close

        :return: None
        """
        # Define a set to remove afterwards
        deleted_vehicles = set()
        # Iterate over the turning vehicles
        for vehicle in self._traffic_light_info['turning_vehicles']['vehicles_passed']:
            # Get vehicle edge
            cur_edge = self._traci.vehicle.getRoadID(vehicle)
            # Check if the vehicle has passed and it is not in the junction edges
            if self.is_vehicle_turning_counted(vehicle) and cur_edge not in self._traffic_light_info['roads']:
                # Append to deleted vehicles list
                deleted_vehicles.add(vehicle)

        # Delete vehicle from turning and passing vehicles
        self._traffic_light_info['vehicles_passed'].difference_update(deleted_vehicles)
        self._traffic_light_info['turning_vehicles']['vehicles_passed'].difference_update(deleted_vehicles)

    """ EXTERNAL COMPONENTS """

    def enable_traffic_analyzer(self, traffic_analyzer: TrafficAnalyzer) -> None:
        """
        Enable the traffic analyzer in the traffic light

        :param traffic_analyzer: traffic light analyzer instance. Default is disabled.
        :type: TrafficAnalyzer
        :return: None
        """
        self._traffic_analyzer = traffic_analyzer

    def publish_analyzer_info(self):
        """
        Publish the analyzed traffic info into the topic related to the traffic light.

        :return: None
        """
        self._mqtt_client.publish(topic=TRAFFIC_ANALYSIS_TOPIC + '/' + self._id,
                                  payload=parse_str_to_valid_schema({self._id: self._traffic_analyzer.traffic_type}))

    def enable_turn_predictor(self, turn_predictor: TurnPredictor) -> None:
        """
        Enable the turn predictor in the traffic light

        :param turn_predictor: turn predictor instance. Default is disabled.
        :type: TurnPredictor
        :return: None
        """
        self._turn_predictor = turn_predictor

    def publish_turn_predictions(self) -> None:
        """
        Publish the turn predictions of each road

        :return: None
        """
        self._mqtt_client.publish(topic=TURN_PREDICTION_TOPIC + '/' + self._id,
                                  payload=parse_str_to_valid_schema(
                                      {self._id: self._turn_predictor.turn_probabilities}))

    def enable_traffic_predictor(self, traffic_predictor: TrafficPredictor) -> None:
        """
        Enable the turn predictor in the traffic light

        :param traffic_predictor: traffic predictor instance. Default is disabled.
        :type: TrafficPredictor
        :return: None
        """
        self._traffic_predictor = traffic_predictor

    def publish_traffic_type_prediction(self) -> None:
        """
        Publish the traffic prediction

        :return: None
        """
        self._mqtt_client.publish(topic=TRAFFIC_PREDICTION_TOPIC + '/' + self._id,
                                  payload=parse_str_to_valid_schema({self._id: self._traffic_predictor.traffic_type}))

    """ TRAFFIC INFO """

    def reset_traffic_counters(self) -> None:
        """
        Reset adjacent traffic info counters

        :return: None
        """
        self._adjacent_traffic_info = {k: '' for k in self._all_ids}

    def publish_contextual_info(self) -> None:
        """
        Publish the traffic light contextual information

        :return: None
        """
        # If it is deployed
        if not self._local:
            self._mqtt_client.publish(topic=TRAFFIC_INFO_TOPIC + '/' + self._id,
                                      payload=parse_str_to_valid_schema(self._publish_info))

    def append_date_contextual_info(self, date_info: dict) -> None:
        """
        Append date information to contextual traffic information and store it on the "publish_info" variable

        :return: None
        """
        self._publish_info = process_payload(traffic_info=self._traffic_light_info, date_info=date_info)

    def reset_contextual_info(self) -> None:
        """
        Restore to default values the traffic light information

        :return: None
        """
        # Store previous vehicles passed and turning
        vehicles_passed, turning_vehicles_passed = self._traffic_light_info['vehicles_passed'], \
                                                   self._traffic_light_info['turning_vehicles']['vehicles_passed']

        # Reset counters to 0, except the roads and the vehicles stored previously
        self._traffic_light_info = {
            'passing_veh_n_s': 0, 'passing_veh_e_w': 0, 'waiting_time_veh_n_s': 0, 'waiting_time_veh_e_w': 0,
            'vehicles_passed': vehicles_passed,
            'turning_vehicles': {'forward': 0, 'right': 0, 'left': 0,
                                 'vehicles_passed': turning_vehicles_passed},
            'roads': self._roads, 'actual_program': self._traci.trafficlight.getProgram(self._id)
        }

    """ MIDDLEWARE """

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
        # Retrieve junction id
        junction_id = str(msg.topic).split('/')[1] if '/' in msg.topic else ''

        if junction_id:
            # Retrieve only the number of passing and turning vehicles
            traffic_info = ast.literal_eval(msg.payload.decode('utf-8')).items()
            # Parse message to dict
            self._adjacent_traffic_info[junction_id] = traffic_info

    def close_connection(self):
        """
        Close MQTT client connection
        """
        self._mqtt_client.loop_stop()

    """ SETTERS AND GETTERS """

    @property
    def id(self) -> str:
        """
        Traffic Light id getter

        :return: id
        :rtype: str
        """
        return self._id

    @property
    def adaptation_strategy(self) -> AdaptationStrategy:
        """
        Adaptation strategy interface getter

        :return: adaptation strategy
        :rtype: AdaptationStrategy
        """
        return self._adaptation_strategy

    @adaptation_strategy.setter
    def adaptation_strategy(self, adaptation_strategy: AdaptationStrategy) -> None:
        """
        Adaptation strategy setter.

        It allows to change the adaptation strategy object at runtime

        :param adaptation_strategy: adaptation strategy
        :type adaptation_strategy: AdaptationStrategy
        :return: None
        """
        self._adaptation_strategy = adaptation_strategy

    @property
    def adjacent_ids(self) -> list:
        """
        Traffic Light Adapter adjacent ids getter

        :return: list of adjacent traffic light ids
        :rtype: list
        """
        return self._adjacent_ids

    @property
    def traffic_light_info(self) -> dict:
        """
        Self traffic light info getter

        :return: traffic light info
        """
        return self._traffic_light_info

    @traffic_light_info.setter
    def traffic_light_info(self, traffic_light_info: dict) -> None:
        """
        Self traffic light info setter.

        :param traffic_light_info: traffic light info
        :type traffic_light_info: dict
        :return: None
        """
        self._traffic_light_info = traffic_light_info

    @property
    def traffic_analyzer(self):
        """
        Traffic Light traffic analyzer getter

        :return: traffic analyzer
        """
        return self._traffic_analyzer

    @property
    def turn_predictor(self):
        """
        Traffic Light turn predictor getter

        :return: turn predictor
        """
        return self._turn_predictor

    @property
    def traffic_predictor(self):
        """
        Traffic Light traffic type predictor getter

        :return: traffic predictor
        """
        return self._traffic_predictor
