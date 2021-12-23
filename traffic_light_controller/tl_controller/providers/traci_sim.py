import ast
import random

import paho.mqtt.client as mqtt
import pandas as pd
import traci
from tl_controller.generators.flows_generator import FlowsGenerator
from tl_controller.providers.analyzer import Analyzer
from tl_controller.providers.utils import get_total_waiting_time_per_lane, get_num_passing_vehicles_detectors
from tl_controller.static.constants import FLOWS_VALUES, FLOWS_OUTPUT_DIR, TL_PROGRAMS, TIMESTEPS_TO_STORE_INFO, \
    TIMESTEPS_PER_HALF_HOUR, MQTT_PORT, MQTT_URL, TRAFFIC_TYPE_TL_ALGORITHMS, PREDICTION_TOPIC, ERROR_THRESHOLD
from tl_controller.time_patterns.time_patterns import TimePattern


class TraCISimulator:
    """
    Dataset generator from the TraCI simulations
    """

    def __init__(self, sumo_conf, time_pattern_file: str = '', mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT,
                 analyzer: bool = False):
        # TODO add time pattern default file
        """
        TraCISimulator initializer.

        :param sumo_conf: SUMO configuration
        :param time_pattern_file: time pattern input file. Default is ''.
        :type time_pattern_file: str
        """

        # Retrieve time pattern file
        self._time_pattern = TimePattern(file_dir=time_pattern_file)

        # SUMO configuration files
        self._config_file = sumo_conf['config_file']
        self._sumo_binary = sumo_conf['sumo_binary']

        # Initialize TraCI simulation to none, to use it in different methods
        self._traci = None
        # TL program to the middle one
        self._tl_program = TL_PROGRAMS[int(len(TL_PROGRAMS) / 2)]
        self._analyzer_tl_program = self._predictor_tl_program = self._predictor_traffic_type = \
            self._analyzer_traffic_type = None

        # Define flow generator and flows default values
        self._flow_generators = FlowsGenerator()
        # High values
        self.high_vehs_per_hour = FLOWS_VALUES['high']['vehsPerHour']
        self.high_vehs_range = FLOWS_VALUES['high']['vehs_range']
        # Medium values
        self.med_vehs_per_hour = FLOWS_VALUES['med']['vehsPerHour']
        self.med_vehs_range = FLOWS_VALUES['med']['vehs_range']
        # Low values
        self.low_vehs_per_hour = FLOWS_VALUES['low']['vehsPerHour']
        self.low_vehs_range = FLOWS_VALUES['low']['vehs_range']
        # Very Low values
        self.very_low_vehs_per_hour = FLOWS_VALUES['very_low']['vehsPerHour']
        self.very_low_vehs_range = FLOWS_VALUES['very_low']['vehs_range']

        # Create Analyzer
        if analyzer:
            self._analyzer = Analyzer()
        else:
            self._analyzer = None

        # Create the MQTT client, its callbacks and its connection to the broker
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self.on_connect
        self._mqtt_client.on_message = self.on_message
        self._mqtt_client.connect(mqtt_url, mqtt_port)
        self._mqtt_client.loop_start()

    def on_connect(self, client, userdata, flags, rc):  # The callback for when the client connects to the broker
        if rc == 0:  # Connection established
            # Subscribe to the traffic prediction topic
            self._mqtt_client.subscribe(PREDICTION_TOPIC)

    def on_message(self, client, userdata, msg):  # The callback for when a PUBLISH message is received from the server.
        # Parse message to dict
        traffic_info = ast.literal_eval(msg.payload.decode('utf-8'))

        # Retrieve predicted traffic type
        traffic_type = int(traffic_info['traffic_prediction'])
        self._predictor_traffic_type = traffic_type

        # Retrieve the best TL program to apply
        self._predictor_tl_program = TRAFFIC_TYPE_TL_ALGORITHMS[str(traffic_type)]

    def simulate(self):
        """
        Perform the simulations by a time pattern with TraCI.

        :return: None
        """
        # Loop over the time pattern simulation
        # Define initial timestep
        cur_timestep = 0

        # We first create the flows file with the loaded time pattern
        self.generate_traffic_flows_by_time_pattern(self._time_pattern.pattern)

        # SUMO is started as a subprocess and then the python script connects and runs
        traci.start([self._sumo_binary, "-c", self._config_file, "--no-warnings"])

        # Store traci instance into the class
        self._traci = traci

        # Load TL program
        for traffic_light in self._traci.trafficlight.getIDList():
            self._traci.trafficlight.setProgram(traffic_light, self._tl_program)

        # Initialize basic data schema
        data = {"tl_id": "c1", "tl_program": self._tl_program, "passing_veh_n_s": 0, "passing_veh_e_w": 0}

        # Initialize the dict
        total_waiting_time = {"c1": {'n': 0, 's': 0, 'e': 0, 'w': 0}}
        prev_total_waiting_time_per_lane = get_total_waiting_time_per_lane(traci)

        # Initialize the set
        vehicles_passed = set()

        if self._analyzer:
            # Get current traffic type with 0 passing vehicles as it is the beginning
            self._analyzer_traffic_type = self._analyzer.analyze_current_traffic_flow(0, 0)

        # Traci simulation
        # Iterate until simulation is ended
        while self._traci.simulation.getMinExpectedNumber() > 0:
            if self._analyzer_tl_program and not self._predictor_tl_program:
                self._tl_program = self._analyzer_tl_program
            elif self._predictor_tl_program and not self._analyzer_tl_program:
                self._tl_program = self._predictor_tl_program
            else:
                # Calculate the difference between the traffic types
                if self._analyzer_traffic_type and self._predictor_traffic_type:
                    error_distance = self._analyzer_traffic_type - self._predictor_traffic_type
                    if abs(error_distance) <= ERROR_THRESHOLD:
                        # The analyzer is right, use its value
                        self._tl_program = self._analyzer_tl_program
                    else:
                        # The analyzer might be wrong, get a "neutral" value -> 1/3 closest to the analyzer as it is in
                        # real time
                        new_traffic_type = int(error_distance / 3 + self._analyzer_traffic_type)
                        if new_traffic_type > 0:
                            self._tl_program = TL_PROGRAMS[new_traffic_type]

            self.apply_tl_program(self._tl_program)

            # Retrieve the current program
            data["tl_program"] = self._traci.trafficlight.getProgram('c1')

            # Waiting time
            current_total_waiting_time = get_total_waiting_time_per_lane(traci)
            # Iterate over the current time on lanes
            for junction, lanes in current_total_waiting_time.items():
                for lane, waiting_time in lanes.items():
                    # Store when the waiting time is calculated
                    if prev_total_waiting_time_per_lane[junction][lane] > waiting_time:
                        # Store by direction
                        if 'n' in lane:
                            if total_waiting_time[junction]['n'] == 0:
                                total_waiting_time[junction]['n'] = prev_total_waiting_time_per_lane[junction][lane]
                            else:
                                total_waiting_time[junction]['n'] += prev_total_waiting_time_per_lane[junction][
                                    lane]
                        if 's' in lane:
                            if total_waiting_time[junction]['s'] == 0:
                                total_waiting_time[junction]['s'] = prev_total_waiting_time_per_lane[junction][lane]
                            else:
                                total_waiting_time[junction]['s'] += prev_total_waiting_time_per_lane[junction][
                                    lane]
                        if 'e' in lane:
                            if total_waiting_time[junction]['e'] == 0:
                                total_waiting_time[junction]['e'] = prev_total_waiting_time_per_lane[junction][lane]
                            else:
                                total_waiting_time[junction]['e'] += prev_total_waiting_time_per_lane[junction][
                                    lane]
                        if 'w' in lane:
                            if total_waiting_time[junction]['w'] == 0:
                                total_waiting_time[junction]['w'] = prev_total_waiting_time_per_lane[junction][lane]
                            else:
                                total_waiting_time[junction]['w'] += prev_total_waiting_time_per_lane[junction][
                                    lane]

            # Update the waiting time per lane
            prev_total_waiting_time_per_lane = current_total_waiting_time

            # Get number of vehicles
            num_passing_vehicles_detectors = get_num_passing_vehicles_detectors(self._traci, vehicles_passed)
            data["passing_veh_e_w"] += num_passing_vehicles_detectors['e_w']
            data["passing_veh_n_s"] += num_passing_vehicles_detectors['n_s']

            # Process data
            data["waiting_time_veh_n_s"] = total_waiting_time['c1']['n'] + total_waiting_time['c1']['s']
            data["waiting_time_veh_e_w"] = total_waiting_time['c1']['w'] + total_waiting_time['c1']['e']

            # Calculate the time pattern id
            time_pattern_id = cur_timestep / TIMESTEPS_PER_HALF_HOUR

            # If next time pattern
            if time_pattern_id.is_integer() and time_pattern_id < len(self._time_pattern.pattern):

                # Store year, month, week, day and hour
                cur_hour = self._time_pattern.get_cur_hour(time_pattern_id)
                if cur_hour:
                    data["hour"] = cur_hour

                cur_day = self._time_pattern.get_cur_day(time_pattern_id)
                if cur_day:
                    data["day"] = cur_day
                else:
                    data["day"] = "monday"

                cur_date_day = self._time_pattern.get_cur_date_day(time_pattern_id)
                if cur_date_day:
                    data["date_day"] = cur_date_day
                else:
                    data["date_day"] = "02"

                cur_week = self._time_pattern.get_cur_week(time_pattern_id)
                if cur_week:
                    data["date_week"] = cur_week
                else:
                    data["date_week"] = "01"

                cur_month = self._time_pattern.get_cur_month(time_pattern_id)
                if cur_month:
                    data["date_month"] = cur_month
                else:
                    data["date_month"] = "02"

                cur_year = self._time_pattern.get_cur_year(time_pattern_id)
                if cur_year:
                    data["date_year"] = cur_year
                else:
                    data["date_year"] = "2021"

            if cur_timestep % TIMESTEPS_TO_STORE_INFO == 0:
                if self._analyzer:
                    # Analyze current traffic
                    self._analyzer_traffic_type = self._analyzer.analyze_current_traffic_flow(data['passing_veh_n_s'],
                                                                                              data['passing_veh_e_w'])
                    self._analyzer_tl_program = TL_PROGRAMS[self._analyzer_traffic_type]

                # Publish data
                self._mqtt_client.publish(topic='traffic_info', payload=str(data).replace('\'', '\"').replace(" ", ""))

                # Reset counters
                data['passing_veh_n_s'] = 0
                data['passing_veh_e_w'] = 0
                total_waiting_time = {"c1": {'n': 0, 's': 0, 'e': 0, 'w': 0}}

            # Simulate a step
            self._traci.simulationStep()

            cur_timestep += 1

        # Close TraCI simulation in order to start another one in the next iteration
        self._traci.close()
        self._mqtt_client.loop_stop()

    def apply_tl_program(self, tl_program: str):
        """
        Apply a new program to the 'c1' junction.

        :param tl_program: new traffic light program
        :type tl_program: str
        :return: None
        """
        # TODO replace to more than a single center 'c1'
        if self._traci.trafficlight.getProgram('c1') != tl_program:
            self._traci.trafficlight.setProgram('c1', tl_program)

    def generate_traffic_flows(self, traffic_type: int, begin: int = 0, end: int = 1800):
        """
        Generate the list of traffic flows based on the traffic type and create the related file.

        Options for traffic_type: \n
        - 0 : Very Low (NS) - Very Low (WE)\n
        - 1 : Very Low (NS) - Low (WE)\n
        - 2 : Low (NS) - Very Low (WE)\n
        - 3 : Low (NS) - Low (WE)\n
        - 4 : Low (NS) - Medium (WE)\n
        - 5 : Low (NS) - High (WE)\n
        - 6 : Medium (NS) - Low (WE)\n
        - 7 : Medium (NS) - Medium (WE)\n
        - 8 : Medium (NS) - High (WE)\n
        - 9 : High (NS) - Low (WE)\n
        - 10 : High (NS) - Medium (WE)\n
        - 11 : High (NS) - High (WE)\n

        :param traffic_type: traffic type.
        :type traffic_type: int
        :param begin: begin timestep per flow. Default is 0
        :type begin: int
        :param end: end timestep per flow. Default is1800
        :type end: int
        :return: None
        """
        # Initialize the flows list
        flows = []

        # The traffic generated will be bidirectional

        # Create the WE traffic
        if traffic_type == 0 or traffic_type == 2:  # Very Low (WE)
            flows.extend([
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.very_low_vehs_per_hour - self.very_low_vehs_range,
                                               self.very_low_vehs_per_hour + self.very_low_vehs_range),
                 'from': 'w1i', 'to': 'e1o'},
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.very_low_vehs_per_hour - self.very_low_vehs_range,
                                               self.very_low_vehs_per_hour + self.very_low_vehs_range),
                 'from': 'e1i', 'to': 'w1o'}
            ])
        elif traffic_type % 3 == 0 or traffic_type == 1:  # Low (WE)
            flows.extend([
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.low_vehs_per_hour - self.low_vehs_range,
                                               self.low_vehs_per_hour + self.low_vehs_range),
                 'from': 'w1i', 'to': 'e1o'},
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.low_vehs_per_hour - self.low_vehs_range,
                                               self.low_vehs_per_hour + self.low_vehs_range),
                 'from': 'e1i', 'to': 'w1o'}
            ])
        elif traffic_type % 3 == 1:  # Medium (WE)
            flows.extend([
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.med_vehs_per_hour - self.med_vehs_range,
                                               self.med_vehs_per_hour + self.med_vehs_range),
                 'from': 'w1i', 'to': 'e1o'},
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.med_vehs_per_hour - self.med_vehs_range,
                                               self.med_vehs_per_hour + self.med_vehs_range),
                 'from': 'e1i', 'to': 'w1o'}
            ])
        elif traffic_type % 3 == 2:  # High (WE)
            flows.extend([
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.high_vehs_per_hour - self.high_vehs_range,
                                               self.high_vehs_per_hour + self.high_vehs_range),
                 'from': 'w1i', 'to': 'e1o'},
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.high_vehs_per_hour - self.high_vehs_range,
                                               self.high_vehs_per_hour + self.high_vehs_range),
                 'from': 'e1i', 'to': 'w1o'}
            ])

        # Create the NS traffic
        if 0 <= traffic_type < 2:  # Very Low values (NS)
            flows.extend([
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.very_low_vehs_per_hour - self.very_low_vehs_range,
                                               self.very_low_vehs_per_hour + self.very_low_vehs_range),
                 'from': 'n1i', 'to': 's1o'},
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.very_low_vehs_per_hour - self.very_low_vehs_range,
                                               self.very_low_vehs_per_hour + self.very_low_vehs_range),
                 'from': 's1i', 'to': 'n1o'}
            ])
        elif 2 <= traffic_type < 6:  # Low values (NS)
            flows.extend([
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.low_vehs_per_hour - self.low_vehs_range,
                                               self.low_vehs_per_hour + self.low_vehs_range),
                 'from': 'n1i', 'to': 's1o'},
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.low_vehs_per_hour - self.low_vehs_range,
                                               self.low_vehs_per_hour + self.low_vehs_range),
                 'from': 's1i', 'to': 'n1o'}
            ])
        elif 6 <= traffic_type < 9:  # Med values (NS)
            flows.extend([
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.med_vehs_per_hour - self.med_vehs_range,
                                               self.med_vehs_per_hour + self.med_vehs_range),
                 'from': 'n1i', 'to': 's1o'},
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.med_vehs_per_hour - self.med_vehs_range,
                                               self.med_vehs_per_hour + self.med_vehs_range),
                 'from': 's1i', 'to': 'n1o'}
            ])
        elif 9 <= traffic_type < 12:  # High values (NS)
            flows.extend([
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.high_vehs_per_hour - self.high_vehs_range,
                                               self.high_vehs_per_hour + self.high_vehs_range),
                 'from': 'n1i', 'to': 's1o'},
                {'begin': begin, 'end': end,
                 'vehsPerHour': random.randint(self.high_vehs_per_hour - self.high_vehs_range,
                                               self.high_vehs_per_hour + self.high_vehs_range),
                 'from': 's1i', 'to': 'n1o'}
            ])

        # TODO also generate random traffic that turns

        # Add flows to the flows generator
        self._flow_generators.add_flows(flows)

    def _store_flows(self):
        # Store the flows
        self._flow_generators.store_flows()
        # Store the flows file at a given position
        self._flow_generators.write_output_file(FLOWS_OUTPUT_DIR)
        # Clean flows from the generator
        self._flow_generators.clean_flows()

    def generate_traffic_flows_by_time_pattern(self, time_pattern: pd.DataFrame):
        for index, row in time_pattern.iterrows():
            self.generate_traffic_flows(traffic_type=row['traffic_type'], begin=index * TIMESTEPS_PER_HALF_HOUR,
                                        end=TIMESTEPS_PER_HALF_HOUR * (index + 1))
        self._store_flows()
