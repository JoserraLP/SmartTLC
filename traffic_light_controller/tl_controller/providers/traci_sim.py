import paho.mqtt.client as mqtt
import traci
from tl_controller.providers.adapter import TrafficLightAdapter
from tl_controller.providers.utils import *
from tl_controller.static.constants import *
from tl_controller.time_patterns.time_patterns import TimePattern


class TraCISimulator:
    """
    Traffic Light Controller class
    """

    def __init__(self, sumo_conf, turn_pattern_file: str, time_pattern_file: str = '', dates: str = '',
                 mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT):
        """
        TraCISimulator initializer.

        :param sumo_conf: SUMO configuration
        :param turn_pattern_file: turn pattern input file.
        :type turn_pattern_file: str
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

        # Define the turn pattern
        self._turn_pattern = TimePattern(file_dir=turn_pattern_file)

        # SUMO configuration files
        self._config_file = sumo_conf['config_file']
        self._sumo_binary = sumo_conf['sumo_binary']

        # Initialize TraCI simulation to none, to use it in different methods
        self._traci, self._topology_rows, self._topology_cols = None, None, None

        # TL program to the middle one
        self._tl_program = TL_PROGRAMS[int(len(TL_PROGRAMS) / 2)]

        # Initialize the Traffic Light Adapter
        self._adapter = TrafficLightAdapter()

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
            # Add save vehicles info parameters, sorted and with the last used route
            add_params = ["--vehroute-output", save_vehicles_dir, "--vehroute-output.last-route", "t",
                          "--vehroute-output.sorted", "t"]
        # Load vehicles info
        elif load_vehicles_dir:
            add_params = ["--route-files", load_vehicles_dir]
        else:
            add_params = ["--route-files", FLOWS_OUTPUT_DIR]

        # Retrieve base params
        sumo_params = [self._sumo_binary, "-c", self._config_file, "--no-warnings"]

        # Extend with additional ones
        sumo_params.extend(add_params)

        # SUMO is started as a subprocess and then the python script connects and runs.
        traci.start(sumo_params)

        # Store traci instance into the class
        self._traci = traci

        # Retrieve network topology
        self._topology_rows, self._topology_cols = get_topology_dim(self._traci)

        # Load TL program
        for traffic_light in self._traci.trafficlight.getIDList():
            self._traci.trafficlight.setProgram(traffic_light, self._tl_program)

        # Initialize basic traffic info schema
        traffic_info = {traffic_light: {'tl_program': '', 'passing_veh_n_s': 0, 'passing_veh_e_w': 0,
                                        'waiting_time_veh_n_s': 0, 'waiting_time_veh_e_w': 0,
                                        'turning_vehicles': {'forward': 0, 'right': 0, 'left': 0},
                                        'veh_passed': set()}
                        for traffic_light in self._traci.trafficlight.getIDList()}

        # Get previous total waiting time per lane
        prev_total_waiting_time_per_lane = get_total_waiting_time_per_lane(traci)

        # Initialize the set for passing veh
        vehicles_passed = {traffic_light: set() for traffic_light in self._traci.trafficlight.getIDList()}

        # Traci simulation
        # Iterate until simulation is ended
        while self._traci.simulation.getMinExpectedNumber() > 0:

            # If vehicles are not loaded means that they need to calculate the new route
            if not load_vehicles_dir:
                # Retrieve turn probabilities from turn pattern
                turn_probabilities = self._turn_pattern.retrieve_turn_prob(timestep=cur_timestep)

                # Update current vehicles routes to enable turns
                # Insert the traffic info to store the number of turning vehicles
                update_route_with_turns(self._traci, traffic_info, rows=self._topology_rows, cols=self._topology_cols,
                                        turn_prob=turn_probabilities)
            else:
                # Otherwise calculate the number of turning vehicles
                calculate_turning_vehicles(self._traci, traffic_info, rows=self._topology_rows,
                                           cols=self._topology_cols)

            # Get new TL programs per traffic light from the adapter
            adapter_tl_programs = self._adapter.get_new_tl_program()

            # If the adapter is available (it returns a dict with TL programs per traffic light)
            if adapter_tl_programs is not None:
                # Apply the new TL program selected by the adapter
                self.apply_tl_programs(adapter_tl_programs)

            # Update number of vehicles passing
            update_passing_vehicles(traci=self._traci, traffic_info=traffic_info, passing_veh=vehicles_passed)

            # Update the current waiting time
            prev_total_waiting_time_per_lane = update_current_waiting_time(traci=self._traci,
                                                                           prev_total_waiting_time_per_lane=
                                                                           prev_total_waiting_time_per_lane,
                                                                           traffic_info=traffic_info,
                                                                           cols=self._topology_cols)

            # Store info each time interval
            if cur_timestep % TIMESTEPS_TO_STORE_INFO == 0:
                # Retrieve date info
                date_info = retrieve_date_info(timestep=cur_timestep, time_pattern=self._time_pattern)

                # Retrieve the veh_passed
                veh_passed = {k: v['veh_passed'] for k, v in traffic_info.items()}

                # Process traffic and date info
                traffic_info_payload = process_payload(traffic_info=traffic_info, date_info=date_info)

                # Publish data
                self._mqtt_client.publish(topic=TRAFFIC_INFO_TOPIC,
                                          payload=parse_str_to_valid_schema(traffic_info_payload))

                # Reset counters, except the vehicles passed set
                traffic_info = {traffic_light: {'tl_program': '', 'passing_veh_n_s': 0, 'passing_veh_e_w': 0,
                                                'waiting_time_veh_n_s': 0, 'waiting_time_veh_e_w': 0,
                                                'turning_vehicles': {'forward': 0, 'right': 0, 'left': 0},
                                                'veh_passed': veh_passed[traffic_light]}
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
