import copy

import paho.mqtt.client as mqtt
from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, TRAFFIC_INFO_TOPIC, TRAFFIC_ANALYSIS_TOPIC, \
    TURN_PREDICTION_TOPIC, TRAFFIC_PREDICTION_TOPIC
from sumo_generators.utils.utils import parse_str_to_valid_schema
from t_predictor.providers.predictor import TrafficPredictor
from tl_controller.providers.adapter import TrafficLightAdapter
from t_analyzer.providers.analyzer import TrafficAnalyzer
from turns_predictor.providers.predictor import TurnPredictor
from tl_controller.providers.utils import process_payload


class TrafficLight:
    """
    Traffic Light class
    """

    def __init__(self, id: str, traci, adapter: TrafficLightAdapter, mqtt_url: str = MQTT_URL,
                 mqtt_port: int = MQTT_PORT, local: bool = False):
        """
        Traffic Light initializer.

        :param id: traffic light junction identifier
        :type id: str
        :param traci: TraCI instance
        :param adapter: traffic light adapter instance
        :type: TrafficLightAdapter
        :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
        :type mqtt_url: str
        :param mqtt_port: MQTT middleware broker port. Default to 1883.
        :type mqtt_port: int
        :param local: flag to execute locally the component. It will not connect to the middleware.
        :type local: bool
        """
        # Store traffic light information
        self._id = id
        self._traci = traci
        self._adapter = adapter

        # Initialize traffic analyzer, turn predictor and traffic predictor to None
        self._traffic_analyzer, self._turn_predictor, self._traffic_predictor = None, None, None

        # Store the local flag
        self._local = local

        # Retrieve adjacent node ids
        self._adjacent_ids = adapter.adjacent_ids

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

        # Initialize publish information, turn predictions and traffic predictions
        self._publish_info, self._turn_predictions, self._traffic_predictions = None, None, None

        # Get the waiting time per lane when the traffic light is created
        self._prev_waiting_time = {lane: traci.lane.getWaitingTime(lane) for lane in
                                   list(dict.fromkeys(traci.trafficlight.getControlledLanes(id)))}

        # Store those detectors related to the traffic light
        self._traffic_light_detectors = [detector for detector in self._traci.inductionloop.getIDList()
                                         if traci.inductionloop.getLaneID(detector).split('_')[1] == id]

        if self._local:
            self._mqtt_client = None
        else:
            # Create the MQTT client and its connection to the broker
            self._mqtt_client = mqtt.Client()
            self._mqtt_client.connect(mqtt_url, mqtt_port)

    # External components utils
    def enable_traffic_analyzer(self, traffic_analyzer: TrafficAnalyzer) -> None:
        """
        Enable the traffic analyzer in the traffic light

        :param traffic_analyzer: traffic light analyzer instance. Default is disabled.
        :type: TrafficAnalyzer
        :return: None
        """
        self._traffic_analyzer = traffic_analyzer

    def enable_turn_predictor(self, turn_predictor: TurnPredictor) -> None:
        """
        Enable the turn predictor in the traffic light

        :param turn_predictor: turn predictor instance. Default is disabled.
        :type: TurnPredictor
        :return: None
        """
        self._turn_predictor = turn_predictor

    def enable_traffic_predictor(self, traffic_predictor: TrafficPredictor) -> None:
        """
        Enable the turn predictor in the traffic light

        :param traffic_predictor: traffic predictor instance. Default is disabled.
        :type: TrafficPredictor
        :return: None
        """
        self._traffic_predictor = traffic_predictor

    # Vehicles utils
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

    def update_tl_program(self) -> None:
        """
        Retrieve the new traffic light program from the adapter and update it.

        :return: None
        """
        # Retrieve traffic type analysis
        traffic_analysis = self.analyze_current_traffic()

        # Retrieve new traffic light program from adapter
        new_program = self._adapter.get_new_tl_program(traffic_analysis)

        # Check if the new program is valid and it is not the same as the actual one
        if new_program and new_program != self._traffic_light_info['actual_program']:
            # Update new program
            self._traci.trafficlight.setProgram(self._id, new_program)

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

    # Analyzer utils
    def analyze_current_traffic(self) -> int:
        """
        Analyze current traffic flow and stores into the analyzer

        :return: analyzed traffic type
        :rtype: int
        """
        return self._traffic_analyzer.analyze_current_traffic_flow(
            passing_veh_n_s=self._traffic_light_info['passing_veh_n_s'],
            passing_veh_e_w=self._traffic_light_info['passing_veh_e_w'])

    def publish_analyzer_info(self):
        """
        Publish the analyzed traffic info into the topic related to the traffic light.

        :return: None
        """
        self._mqtt_client.publish(topic=TRAFFIC_ANALYSIS_TOPIC + '/' + self._id,
                                  payload=parse_str_to_valid_schema(self._traffic_analyzer.traffic_type))

    # Turn predictor utils
    def predict_turn_probabilities(self, date_info: dict) -> None:
        """
        Predicts the turn probabilities based on a road and a date

        :param date_info: date information (hour, day, month and year)
        :type date_info: dict
        :return: None
        """
        # Copy the date info into a dict
        traffic_info = copy.deepcopy(date_info)

        # Remove day from traffic info
        del traffic_info['day']

        # Add the roads to the traffic info
        traffic_info.update({'roads': self._roads})

        # Retrieve turn predictions
        self._turn_predictions = self._turn_predictor.predict_turn_probabilities(traffic_info=traffic_info)

    def publish_turn_predictions(self) -> None:
        """
        Publish the turn predictions of each road

        :return: None
        """
        self._mqtt_client.publish(topic=TURN_PREDICTION_TOPIC + '/' + self._id,
                                  payload=parse_str_to_valid_schema(self._turn_predictions))

    # Traffic predictor utils
    def predict_traffic_type(self, date_info: dict) -> None:
        """
        Predicts the traffic prediction based on a junction and a date

        :param date_info: date information (hour, day, month and year)
        :type date_info: dict
        :return: None

        :return: None
        """

        # Copy the date info into a dict
        traffic_info = copy.deepcopy(date_info)

        # Add the roads to the traffic info
        traffic_info.update(self._traffic_light_info)

        # Remove vehicles passed as it is not used on the training process
        traffic_info.pop('vehicles_passed')

        # Retrieve traffic predictions
        self._traffic_predictions = self._traffic_predictor.predict_traffic_type(traffic_info=traffic_info)

    def publish_traffic_type_prediction(self) -> None:
        """
        Publish the traffic prediction

        :return: None
        """
        self._mqtt_client.publish(topic=TRAFFIC_PREDICTION_TOPIC + '/' + self._id,
                                  payload=parse_str_to_valid_schema(self._traffic_predictions))

    # Adapter utils
    def close_adapter_connection(self) -> None:
        """
        Close Traffic Light Adapter middleware connection

        :return: None
        """
        self.adapter.close_connection()

    @property
    def id(self) -> str:
        """
        Traffic Light id getter

        :return: id
        :rtype: str
        """
        return self._id

    @property
    def adjacent_ids(self) -> list:
        """
        Adjacent ids getter

        :return: adjacent ids
        :rtype: list
        """
        return self._adjacent_ids

    @property
    def adapter(self):
        """
        Traffic Light adapter getter

        :return: traffic light adapter
        """
        return self._adapter

    @property
    def traffic_light_info(self) -> dict:
        """
        Traffic Light info getter

        :return: traffic light info
        :rtype: dict
        """
        return self._traffic_light_info

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
