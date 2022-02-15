import math
import random

import paho.mqtt.client as mqtt
import pandas as pd
import traci
from tl_controller.generators.flows_generator import FlowsGenerator
from tl_controller.providers.adapter import TrafficLightAdapter
from tl_controller.providers.utils import get_total_waiting_time_per_lane, get_num_passing_vehicles_detectors, \
    update_route_with_turns, get_topology_dim, calculate_turning_vehicles
from tl_controller.static.constants import FLOWS_VALUES, FLOWS_OUTPUT_DIR, TL_PROGRAMS, TIMESTEPS_TO_STORE_INFO, \
    TIMESTEPS_PER_HALF_HOUR, MQTT_PORT, MQTT_URL, DEFAULT_TIME_PATTERN_FILE
from tl_controller.time_patterns.time_patterns import TimePattern


class TraCISimulator:
    """
    Traffic Light Controller class
    """

    def __init__(self, sumo_conf, time_pattern_file: str = '', dates: str = '', mqtt_url: str = MQTT_URL,
                 mqtt_port: int = MQTT_PORT):
        """
        TraCISimulator initializer.

        :param sumo_conf: SUMO configuration
        :param time_pattern_file: time pattern input file. Default is ''.
        :type time_pattern_file: str
        :param dates: time pattern input file. Default is ''.
        :type dates: str
        :param mqtt_url: MQTT middleware broker url. Default to '172.20.0.2'.
        :type mqtt_url: str
        :param mqtt_port: MQTT middleware broker port. Default to 1883.
        :type mqtt_port: int
        """

        if time_pattern_file != '':
            # Retrieve time pattern file
            self._time_pattern = TimePattern(file_dir=time_pattern_file)
        elif dates != '':
            # Retrieve time pattern from given dates
            self._dates = dates
            self._time_pattern = TimePattern(file_dir=DEFAULT_TIME_PATTERN_FILE)
            start_date, end_date = dates.split('-')
            self._time_pattern.retrieve_pattern_days(start_date=start_date, end_date=end_date)

        # SUMO configuration files
        self._config_file = sumo_conf['config_file']
        self._sumo_binary = sumo_conf['sumo_binary']

        # Initialize TraCI simulation to none, to use it in different methods
        self._traci = None
        # TL program to the middle one
        self._tl_program = TL_PROGRAMS[int(len(TL_PROGRAMS) / 2)]

        # Initialize the Traffic Light Adapter
        self._adapter = TrafficLightAdapter()

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

        # Create the MQTT client, its callbacks and its connection to the broker
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.connect(mqtt_url, mqtt_port)
        self._mqtt_client.loop_start()

    def simulate(self, load_vehicles_dir: str = '', save_vehicles_dir: str = ''):
        """
        Perform the simulations by a time pattern with TraCI.

        :return: None
        """
        # Loop over the time pattern simulation
        # Define initial timestep
        cur_timestep = 0

        # Save vehicles info
        if save_vehicles_dir:
            # Add save vehicles info parameters
            add_params = ["--vehroute-output", save_vehicles_dir, "--vehroute-output.last-route", "t",
                          "--vehroute-output.sorted", "t"]
        # Load vehicles info
        elif load_vehicles_dir:
            add_params = ["--route-files", load_vehicles_dir]
        else:
            add_params = []

        # Retrieve base params
        sumo_params = [self._sumo_binary, "-c", self._config_file, "--no-warnings"]

        # Extend with additional ones
        sumo_params.extend(add_params)

        # SUMO is started as a subprocess and then the python script connects and runs. Add the additional params
        traci.start(sumo_params)

        # Store traci instance into the class
        self._traci = traci

        # If the vehicles are not loaded previously, generate them
        if not load_vehicles_dir:
            # Create the flows file with the loaded time pattern
            self.generate_traffic_flows_by_time_pattern(self._time_pattern.pattern)

        # Load TL program
        for traffic_light in self._traci.trafficlight.getIDList():
            self._traci.trafficlight.setProgram(traffic_light, self._tl_program)

        topology_dim = get_topology_dim(self._traci)

        # Initialize basic traffic info schema
        traffic_info = {traffic_light: {'tl_program': '', 'passing_veh_n_s': 0, 'passing_veh_e_w': 0,
                                        'waiting_time_veh_n_s': 0, 'waiting_time_veh_e_w': 0,
                                        'turning_vehicles': {'forward': 0, 'right': 0, 'left': 0}}
                        for traffic_light in self._traci.trafficlight.getIDList()}

        # Get previous total waiting time per lane
        prev_total_waiting_time_per_lane = get_total_waiting_time_per_lane(traci)

        # Initialize the set
        vehicles_passed = {traffic_light: set() for traffic_light in self._traci.trafficlight.getIDList()}

        # Traci simulation
        # Iterate until simulation is ended
        while self._traci.simulation.getMinExpectedNumber() > 0:

            # If vehicles are not loaded means that they need to calculate the new route
            if not load_vehicles_dir:
                # Update current vehicles routes to enable turns
                # Insert the traffic info to store the number of turning vehicles
                update_route_with_turns(self._traci, traffic_info)
            else:
                # Otherwise calculate the number of turning vehicles
                calculate_turning_vehicles(self._traci, traffic_info)

            # Get new TL programs per traffic light from the adapter
            adapter_tl_programs = self._adapter.get_new_tl_program()

            # If the adapter is available (it returns a dict with TL programs per traffic light)
            if adapter_tl_programs is not None:
                # Apply the new TL program selected by the adapter
                self.apply_tl_programs(adapter_tl_programs)

            num_passing_vehicles_detectors = get_num_passing_vehicles_detectors(self._traci, vehicles_passed)

            # Update number of vehicles passing
            for traffic_light, info in num_passing_vehicles_detectors.items():
                # Increase the direction counters
                traffic_info[traffic_light]['passing_veh_n_s'] += info['north'] + info['south']
                traffic_info[traffic_light]['passing_veh_e_w'] += info['east'] + info['west']

            # Waiting time
            current_total_waiting_time = get_total_waiting_time_per_lane(traci)
            # Iterate over the current time on lanes
            for junction, lanes in current_total_waiting_time.items():
                for lane, waiting_time in lanes.items():
                    # Store when the waiting time is calculated
                    if prev_total_waiting_time_per_lane[junction][lane] > waiting_time:
                        # Store by direction
                        if 'n' in lane or 's' in lane:
                            traffic_info[junction]['waiting_time_veh_n_s'] += \
                                prev_total_waiting_time_per_lane[junction][lane]
                        if 'e' in lane or 'w' in lane:
                            traffic_info[junction]['waiting_time_veh_e_w'] += \
                                prev_total_waiting_time_per_lane[junction][lane]
                        elif 'c' in lane:
                            # Retrieve the traffic lights
                            prev_traffic_light, next_traffic_light, _ = lane.split('_')

                            # Get the TL identifiers
                            prev_tl_id = int(prev_traffic_light[1:])
                            next_tl_id = int(next_traffic_light[1:])

                            # North-South
                            if prev_tl_id + topology_dim == next_tl_id or prev_tl_id - topology_dim == next_tl_id:
                                traffic_info[junction]['waiting_time_veh_n_s'] += \
                                    prev_total_waiting_time_per_lane[junction][lane]
                            # East-West
                            elif prev_tl_id + 1 == next_tl_id or prev_tl_id - 1 == next_tl_id:
                                traffic_info[junction]['waiting_time_veh_e_w'] += \
                                    prev_total_waiting_time_per_lane[junction][lane]

            # Update the waiting time per lane
            prev_total_waiting_time_per_lane = current_total_waiting_time

            # Store info each time interval
            if cur_timestep % TIMESTEPS_TO_STORE_INFO == 0:

                # Calculate the time pattern id
                time_pattern_id = math.floor(cur_timestep / TIMESTEPS_PER_HALF_HOUR)

                date_info = dict()

                # If next time pattern
                if time_pattern_id < len(self._time_pattern.pattern):

                    # Store year, month, week, day and hour
                    cur_hour = self._time_pattern.get_cur_hour(time_pattern_id)
                    if cur_hour:
                        date_info["hour"] = cur_hour

                    cur_day = self._time_pattern.get_cur_day(time_pattern_id)
                    if cur_day:
                        date_info["day"] = cur_day
                    else:
                        date_info["day"] = "monday"

                    cur_date_day = self._time_pattern.get_cur_date_day(time_pattern_id)
                    if cur_date_day:
                        date_info["date_day"] = cur_date_day
                    else:
                        date_info["date_day"] = "02"

                    cur_month = self._time_pattern.get_cur_month(time_pattern_id)
                    if cur_month:
                        date_info["date_month"] = cur_month
                    else:
                        date_info["date_month"] = "02"

                    cur_year = self._time_pattern.get_cur_year(time_pattern_id)
                    if cur_year:
                        date_info["date_year"] = cur_year
                    else:
                        date_info["date_year"] = "2021"

                # Format to be Telegraf valid
                traffic_info_payload = list()
                for traffic_light_id, tl_info in traffic_info.items():
                    # Store the concatenation of both dicts
                    traffic_info_payload.append(dict({'tl_id': traffic_light_id}, **dict(tl_info), **dict(date_info)))

                # Publish data
                self._mqtt_client.publish(topic='traffic_info', payload=str(traffic_info_payload).replace('\'', '\"')
                                          .replace(" ", ""))

                # Reset counters
                traffic_info = {traffic_light: {'tl_program': '', 'passing_veh_n_s': 0, 'passing_veh_e_w': 0,
                                                'waiting_time_veh_n_s': 0, 'waiting_time_veh_e_w': 0,
                                                'turning_vehicles': {'forward': 0, 'right': 0, 'left': 0}}
                                for traffic_light in self._traci.trafficlight.getIDList()}

            # Simulate a step
            self._traci.simulationStep()

            # Increase simulation step
            cur_timestep += 1

        # Close TraCI simulation, the adapter connection and the MQTT client
        self._traci.close()
        self._adapter.close_connection()
        self._mqtt_client.loop_stop()

    def apply_tl_programs(self, tl_programs: dict):
        """
        Apply a new program to each traffic light in the topology.

        :param tl_programs: new traffic light program per traffic light dict
        :type tl_programs: dict
        :return: None
        """
        for traffic_light, program in tl_programs.items():
            if self._traci.trafficlight.getProgram(traffic_light) != program:
                self._traci.trafficlight.setProgram(traffic_light, program)

    def generate_traffic_flows(self, traffic_type: int, begin: int = 0, end: int = TIMESTEPS_PER_HALF_HOUR):
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
        :param begin: begin timestep per flow. Default is 0.
        :type begin: int
        :param end: end timestep per flow. Default is 1800.
        :type end: int
        :return: None
        """
        # Initialize the flows list
        flows = []

        dim = get_topology_dim(self._traci)

        lower_bound, upper_bound = -1, -1

        # The traffic generated will be bidirectionally
        # Create the WE traffic
        if traffic_type == 0 or traffic_type == 2:  # Very Low (WE)
            lower_bound = self.very_low_vehs_per_hour - self.very_low_vehs_range
            upper_bound = self.very_low_vehs_per_hour + self.very_low_vehs_range
        elif traffic_type % 3 == 0 or traffic_type == 1:  # Low (WE)
            lower_bound = self.low_vehs_per_hour - self.low_vehs_range
            upper_bound = self.low_vehs_per_hour + self.low_vehs_range
        elif traffic_type % 3 == 1:  # Medium (WE)
            lower_bound = self.med_vehs_per_hour - self.med_vehs_range
            upper_bound = self.med_vehs_per_hour + self.med_vehs_range
        elif traffic_type % 3 == 2:  # High (WE)
            lower_bound = self.high_vehs_per_hour - self.high_vehs_range
            upper_bound = self.high_vehs_per_hour + self.high_vehs_range

        # From external to center
        flows.extend([
            {'begin': begin, 'end': end,
             'vehsPerHour': random.randint(lower_bound, upper_bound),
             'from': f'w{i}_c{dim * i - dim + 1}', 'to': f'c{dim * i}_e{i}'} for i in range(1, dim + 1)])

        # From center to external
        flows.extend([
            {'begin': begin, 'end': end,
             'vehsPerHour': random.randint(lower_bound, upper_bound),
             'from': f'e{i}_c{dim * i}', 'to': f'c{dim * i - dim + 1}_w{i}'} for i in range(1, dim + 1)])

        # Create the NS traffic
        if 0 <= traffic_type < 2:  # Very Low values (NS)
            lower_bound = self.very_low_vehs_per_hour - self.very_low_vehs_range
            upper_bound = self.very_low_vehs_per_hour + self.very_low_vehs_range
        elif 2 <= traffic_type < 6:  # Low values (NS)
            lower_bound = self.low_vehs_per_hour - self.low_vehs_range
            upper_bound = self.low_vehs_per_hour + self.low_vehs_range
        elif 6 <= traffic_type < 9:  # Med values (NS)
            lower_bound = self.med_vehs_per_hour - self.med_vehs_range
            upper_bound = self.med_vehs_per_hour + self.med_vehs_range
        elif 9 <= traffic_type < 12:  # High values (NS)
            lower_bound = self.high_vehs_per_hour - self.high_vehs_range
            upper_bound = self.high_vehs_per_hour + self.high_vehs_range

        # From external to center
        flows.extend([
            {'begin': begin, 'end': end,
             'vehsPerHour': random.randint(lower_bound, upper_bound),
             'from': f'n{i}_c{dim * (dim - 1) + i}', 'to': f'c{i}_s{i}'} for i in range(1, dim + 1)])

        # From center to external
        flows.extend([
            {'begin': begin, 'end': end,
             'vehsPerHour': random.randint(lower_bound, upper_bound),
             'from': f's{i}_c{i}', 'to': f'c{dim * (dim - 1) + i}_n{i}'} for i in range(1, dim + 1)])

        # Add flows to the flows generator
        self._flow_generators.add_flows(flows)

    def _store_flows(self):
        """
        Store the flows into the default output file.

        :return: None
        """
        # Store the flows
        self._flow_generators.store_flows()
        # Store the flows file at a given position
        self._flow_generators.write_output_file(FLOWS_OUTPUT_DIR)
        # Clean flows from the generator
        self._flow_generators.clean_flows()

    def generate_traffic_flows_by_time_pattern(self, time_pattern: pd.DataFrame):
        """
        Generate the traffic flows and store it on the output file.

        :param time_pattern: dataframe with the time pattern.
        :type time_pattern: pd.DataFrame
        :return: None
        """
        # Iter over the time pattern rows
        for index, row in time_pattern.iterrows():
            # Generate the row traffic flow
            self.generate_traffic_flows(traffic_type=row['traffic_type'], begin=index * TIMESTEPS_PER_HALF_HOUR,
                                        end=TIMESTEPS_PER_HALF_HOUR * (index + 1))
        # Store the flows in the output file
        self._store_flows()
