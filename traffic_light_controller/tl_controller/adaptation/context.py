import ast

import paho.mqtt.client as mqtt

from sumo_generators.network.net_topology import NetworkTopology
from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, TRAFFIC_INFO_TOPIC, \
    TRAFFIC_ANALYSIS_TOPIC, TURN_PREDICTION_TOPIC, TRAFFIC_PREDICTION_TOPIC
from sumo_generators.utils.utils import parse_to_valid_schema
from t_analyzer.providers.analyzer import TrafficAnalyzer
from t_predictor.providers.predictor import TrafficPredictor
from tl_controller.adaptation.strategy import AdaptationStrategy
from tl_controller.storage.storage import TrafficLightInfoStorage
from turns_predictor.providers.predictor import TurnPredictor


class TrafficLightAdapter:
    """
    The Traffic Light Adapter defines the interface of interest and stores other relevant information
    """

    def __init__(self, adaptation_strategy: AdaptationStrategy, net_topology: NetworkTopology, traci, tl_id: str,
                 mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT, local: bool = False) -> None:
        """
        Traffic Light Adapter initializer.

        :param adaptation_strategy: adaptation concrete strategy
        :type adaptation_strategy: AdaptationStrategy
        :param net_topology: network topology
        :type net_topology: NetworkTopology
        :param traci: TraCI instance
        :param tl_id: traffic light junction identifier
        :type tl_id: str
        :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
        :type mqtt_url: str
        :param mqtt_port: MQTT middleware broker port. Default to 1883.
        :type mqtt_port: int
        :param local: flag to execute locally the component. It will not connect to the middleware.
        :type local: bool
        """
        # Store the adaptation strategy
        self._adaptation_strategy = adaptation_strategy

        # Store parameter values
        self._local, self._tl_id, self._traci = local, tl_id, traci

        # Initialize traffic analyzer, turn predictor and traffic predictor to None
        self._traffic_analyzer, self._turn_predictor, self._traffic_predictor = None, None, None

        # Initialize temporal window to 0
        self._cur_temporal_window = 0

        # Store network topology db connection
        self._net_topology = net_topology

        # Retrieve connected roads from the database
        self._outbound_roads, self._inbound_roads = self._net_topology.get_tl_roads(tl_name=self._tl_id)

        # Roads used primarily are the inbound roads to calculate the required information.

        # Gather only local TL information
        self._traffic_light_info = {self._tl_id: TrafficLightInfoStorage(tl_id=self._tl_id,
                                                                         roads=self._inbound_roads)}

        # Get the waiting time per inbound lane when the traffic light is created
        self._prev_waiting_time = {lane.name: 0 for lane in self._inbound_roads}

        # Get traffic light related detectors
        self._traffic_light_detectors = net_topology.get_junction_detectors(junction_name=self._tl_id)

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

    def update_tl_program(self, timestep: int) -> None:
        """
        Traffic Light Adapter delegates on the adaptation strategy the retrieval of the new traffic light

        :param timestep: simulation timestep
        :type timestep: int
        :return: None
        """

        # Get new traffic light algorithm based on the adaptation strategy
        new_tl_program = self._adaptation_strategy.get_new_tl_program(traffic_info=self._traffic_light_info,
                                                                      timestep=timestep,
                                                                      temporal_window=self._cur_temporal_window)

        # Check if the new program is valid and it is not the same as the actual one
        if new_tl_program and new_tl_program != self._traffic_light_info[self._tl_id].actual_program:
            # Update new program
            self._traci.trafficlight.setProgram(self._tl_id, new_tl_program)

    """ VEHICLE UTILS """

    def count_passing_vehicles(self) -> None:
        """
        Update the counters of vehicles passing on each queue, appending them to the list
        
        :return: None
        """

        # Iterate over the traffic light detectors
        for detector in self._traffic_light_detectors:
            # Road where the detector is placed
            lane = str(detector).replace('e1detector_', '')

            # Get the current passing vehicles
            cur_veh = set(self._traci.inductionloop.getLastStepVehicleIDs(detector))

            # Calculate the difference between the sets
            not_counted_veh = cur_veh - self._traffic_light_info[self._tl_id].vehicles_passed

            # If there are no counted vehicles
            if not_counted_veh:
                # Append the not counted vehicles
                self._traffic_light_info[self._tl_id].update_passing_vehicles(passing_veh=not_counted_veh)

                # Add the number of non-counted vehicles
                self._traffic_light_info[self._tl_id].increase_passing_vehicles(queue=lane,
                                                                                num_veh=len(not_counted_veh))

    def calculate_waiting_time_per_lane(self) -> None:
        """
        Calculate and update the waiting time per lane.

        :return: None
        """
        # Calculate current waiting time
        current_waiting_time = {lane.name: self._traci.lane.getWaitingTime(lane.name) for lane in self._inbound_roads}

        # Iterate over the lanes
        for lane, waiting_time in current_waiting_time.items():
            # If the information is valid (there are no more vehicles waiting)
            if self._prev_waiting_time[lane] > waiting_time:
                # Append to queue
                self._traffic_light_info[self._tl_id].increase_waiting_time(queue=lane,
                                                                            waiting_time=self._prev_waiting_time[lane])

        # Update the previous waiting time to the current waiting time
        self._prev_waiting_time = current_waiting_time

    def calculate_emissions_per_lane(self) -> None:
        """
        Calculate the emissions per lane.

        :return: dict
        """
        # Iterate over the lanes
        for lane in self._inbound_roads:

            # Store lane info dict
            lane_dict = {'occupancy': self._traci.lane.getLastStepOccupancy(lane.name),
                         'CO2_emission': self._traci.lane.getCO2Emission(lane.name),
                         'CO_emission': self._traci.lane.getCOEmission(lane.name),
                         'HC_emission': self._traci.lane.getHCEmission(lane.name),
                         'PMx_emission': self._traci.lane.getPMxEmission(lane.name),
                         'NOx_emission': self._traci.lane.getNOxEmission(lane.name),
                         'noise_emission': self._traci.lane.getNoiseEmission(lane.name)}

            # Insert into the historical info
            for k, v in lane_dict.items():
                self._traffic_light_info[self._tl_id].append_item_on_list_queue(queue=lane.name, name=k, value=v)

    def remove_passing_vehicles(self) -> None:
        """
        Remove those vehicles that have passed on a edge close to the junction but it is not anymore close

        :return: None
        """
        # Define a set to remove afterwards
        deleted_vehicles = set()
        # Iterate over the turning vehicles
        for vehicle in self._traffic_light_info[self._tl_id].turning_vehicles_passed:
            # Get vehicle edge
            cur_edge = self._traci.vehicle.getRoadID(vehicle)
            # Check if the vehicle has passed and it is not in the junction edges
            if self._traffic_light_info[self._tl_id].is_vehicle_turning_counted(vehicle) and \
                    cur_edge not in self._traffic_light_info[self._tl_id].roads:
                # Append to deleted vehicles list
                deleted_vehicles.add(vehicle)

        # Delete vehicle from turning and passing vehicles
        self._traffic_light_info[self._tl_id].remove_passed_vehicles(vehicles=deleted_vehicles)

    def is_vehicle_turning_counted(self, vehicle_id: str) -> bool:
        """
        Check if a turning vehicles has been counted previously

        :param vehicle_id: vehicle identifier
        :type vehicle_id: str
        :return: True if it is counted, False otherwise
        :rtype: bool
        """
        return self._traffic_light_info[self._tl_id].is_vehicle_turning_counted(vehicle_id=vehicle_id)

    def increase_turning_vehicles(self, turn: str) -> None:
        """
        Increase the number of turning vehicles by 1 on the given turn

        :param turn: turn direction
        :type turn: str
        :return: None
        """
        self._traffic_light_info[self._tl_id].increase_turning_vehicles(turn)

    def append_turning_vehicle(self, vehicle_id: str) -> None:
        """
        Append a vehicle to the list of turning vehicles of the traffic light

        :param vehicle_id: vehicle identifier
        :type vehicle_id: str
        :return: None
        """
        self._traffic_light_info[self._tl_id].append_turning_vehicle(vehicle_id=vehicle_id)

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
        if self._traffic_analyzer:
            # Parsed dict to str to use the valid schema
            self._mqtt_client.publish(topic=TRAFFIC_ANALYSIS_TOPIC + '/' + self._tl_id,
                                      payload=parse_to_valid_schema(
                                          str({self._tl_id: self._traffic_analyzer.traffic_type})))

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
        if self._turn_predictor:
            # Parsed dict to str to use the valid schema
            self._mqtt_client.publish(topic=TURN_PREDICTION_TOPIC + '/' + self._tl_id,
                                      payload=parse_to_valid_schema(
                                          str({self._tl_id: self._turn_predictor.turn_probabilities})))

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
        if self._traffic_predictor:
            # Parsed dict to str to use the valid schema
            self._mqtt_client.publish(topic=TRAFFIC_PREDICTION_TOPIC + '/' + self._tl_id,
                                      payload=parse_to_valid_schema(
                                          str({self._tl_id: self._traffic_predictor.traffic_type})))

    """ TRAFFIC INFO """

    def insert_date_info(self, temporal_window: int, date_info: dict) -> None:
        """
        Insert date information to current traffic light info at a given temporal window

        :param temporal_window: temporal window identifier
        :type temporal_window: int
        :param date_info: simulation date information 
        :type date_info: dict
        :return: None
        """
        # Insert the date info for the current traffic light at a given temporal window 
        self._traffic_light_info[self._tl_id].insert_date_info(temporal_window=temporal_window, date_info=date_info)

    def increase_temporal_window(self):
        self._cur_temporal_window += 1
        self._traffic_light_info[self._tl_id].increase_temporal_window()

    def publish_contextual_info(self, contextual_tl_info: dict) -> None:
        """
        Publish the traffic light contextual information into the middleware and store it into the db

        :param contextual_tl_info: contextual traffic light info
        :type contextual_tl_info: dict
        :return: None
        """
        # If it is deployed
        if not self._local:

            # Publish info appending tag 'info' for Telegraf
            self._mqtt_client.publish(topic=TRAFFIC_INFO_TOPIC + '/' + self._tl_id,
                                      payload=parse_to_valid_schema(contextual_tl_info))

    def get_traffic_info_by_temporal_window(self, temporal_window: int):
        """
        Get local traffic info by selected temporal window
        """
        return self._traffic_light_info[self._tl_id].get_traffic_info_by_temporal_window(
            temporal_window=temporal_window)

    def get_processed_contextual_info(self) -> None:
        """
        Get processed contextual info for current temporal window, with average values
        """
        return self._traffic_light_info[self._tl_id].get_processed_contextual_info(temporal_window=
                                                                                   self._cur_temporal_window)

    def create_historical_traffic_info(self, temporal_window: int, queue_info: dict = None) -> None:
        """
        Creates a new entry for the historical info for the timestep

        :param temporal_window: current info temporal window
        :type temporal_window: int
        :param queue_info: number of passing vehicles, waiting time and turning vehicles per queue.
        :type queue_info: dict

        :return: None
        """
        self._traffic_light_info[self._tl_id].create_historical_traffic_info(temporal_window=temporal_window,
                                                                             queue_info=queue_info)

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
            pass

    def on_message(self, client, userdata, msg):
        """
        Callback called when the client receives a message from to the broker.
        :param client: MQTT client
        :param userdata: MQTT client data
        :param msg: message received from the middleware
        :return: None
        """
        pass

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
        return self._tl_id

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

    @property
    def traffic_light_info(self):
        """
        Traffic Light info getter

        :return: traffic light info instance
        """
        return self._traffic_light_info

    @property
    def temporal_window(self):
        """
        Traffic Light temporal window getter

        :return: traffic light temporal window
        """
        return self._cur_temporal_window

    @temporal_window.setter
    def temporal_window(self, temporal_window: int):
        """
        Traffic Light temporal window setter

        :param temporal_window: traffic light temporal window
        :type temporal_window: int
        """
        self._cur_temporal_window = temporal_window
