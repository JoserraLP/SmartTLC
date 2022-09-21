import paho.mqtt.client as mqtt
import traci
from sumo_generators.time_patterns.time_patterns import TimePattern
from sumo_generators.time_patterns.utils import retrieve_date_info
from sumo_generators.utils.utils import parse_str_to_valid_schema
from tl_controller.providers.adapter import TrafficLightAdapter
from tl_controller.providers.traffic_light import TrafficLight
from tl_controller.providers.utils import *
from tl_controller.static.constants import *
from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, TRAFFIC_INFO_TOPIC, TIMESTEPS_PER_HALF_HOUR, \
    TIMESTEPS_TO_STORE_INFO


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
        if turn_pattern_file:
            self._turn_pattern = TimePattern(file_dir=turn_pattern_file)
        else:
            self._turn_pattern = None

        # SUMO configuration files
        self._config_file = sumo_conf['config_file']
        self._sumo_binary = sumo_conf['sumo_binary']

        # Initialize TraCI simulation to none, to use it in different methods
        self._traci, self._topology_rows, self._topology_cols, self._topology_network = None, None, None, None
        # TL program to the middle one
        self._tl_program = TL_PROGRAMS[int(len(TL_PROGRAMS) / 2)]

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

        # Get maximum timesteps
        max_timesteps = len(self._time_pattern.pattern) * TIMESTEPS_PER_HALF_HOUR

        # Save vehicles info
        if save_vehicles_dir:
            # Add save vehicles info parameters, sorted and with the last used route.
            add_params = ["--vehroute-output", save_vehicles_dir, "--vehroute-output.last-route", "t",
                          "--vehroute-output.sorted", "t", "--route-files", FLOWS_OUTPUT_DIR]
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

        # Load TL programs
        for traffic_light in self._traci.trafficlight.getIDList():
            self._traci.trafficlight.setProgram(traffic_light, self._tl_program)

        # Retrieve network topology
        self._topology_rows, self._topology_cols = get_topology_dim(self._traci)

        # Retrieve all edges
        edges = [edge for edge in self._traci.edge.getIDList() if ':' not in edge]

        # Define and generate the network graph
        net_graph = NetGraph(num_rows=self._topology_rows, num_cols=self._topology_cols, valid_edges=edges)
        net_graph.generate_graph()

        # Initialize Traffic Lights and its adapters
        traffic_lights = {traffic_light: TrafficLight(id=traffic_light, traci=traci,
                                                      adapter=TrafficLightAdapter(net_graph=net_graph, id=traffic_light,
                                                                                  rows=self._topology_rows,
                                                                                  cols=self._topology_cols))
                          for traffic_light in self._traci.trafficlight.getIDList()}

        # Append traffic global information
        summary_waiting_time, summary_veh_passed = 0, 0

        # Traci simulation. Iterate until simulation is ended
        while cur_timestep < max_timesteps:

            # Here the global controller signalises the traffic lights to perform different actions
            # Signal each traffic light to perform its own adaptation process
            for traffic_light_id, traffic_light in traffic_lights.items():
                # 1. Update the traffic light program based on the adapter
                traffic_light.update_tl_program()

                # 2. Remove previous passing vehicles
                traffic_light.remove_passing_vehicles()

                # 3. Count number of vehicles passing
                traffic_light.count_passing_vehicles()

                # 4. Update waiting time per lane on each junction
                traffic_light.calculate_waiting_time_per_lane(cols=self._topology_cols)

            # Check if turns are enabled
            if self._turn_pattern:
                # If vehicles are not loaded means that they need to calculate the new route
                if not load_vehicles_dir:
                    # Retrieve turn probabilities by edges
                    turn_prob_by_edges = retrieve_turn_prob_by_edge(traci=traci,
                                                                    turn_prob=self._turn_pattern.retrieve_turn_prob
                                                                    (simulation_timestep=cur_timestep))

                    # Update current vehicles routes to enable turns
                    # Insert the traffic info to store the number of turning vehicles
                    update_route_with_turns(self._traci, net_graph=net_graph, traffic_lights=traffic_lights,
                                            turn_prob_by_edges=turn_prob_by_edges)

                else:

                    # Otherwise calculate the number of turning vehicles
                    calculate_turning_vehicles(self._traci, traffic_lights=traffic_lights, net_graph=net_graph)

            # Store info each time interval
            if cur_timestep % TIMESTEPS_TO_STORE_INFO == 0:

                # Retrieve date info
                date_info = retrieve_date_info(timestep=cur_timestep, time_pattern=self._time_pattern)

                # Iterate over each traffic light, retrieve its information and signalize to publish them
                for traffic_light_id, traffic_light in traffic_lights.items():
                    # Retrieve traffic light information
                    traffic_light_info = traffic_light.traffic_light_info

                    # Store summary of waiting time and vehicles passed
                    summary_waiting_time += traffic_light_info['waiting_time_veh_n_s'] + \
                                            traffic_light_info['waiting_time_veh_e_w']
                    summary_veh_passed += traffic_light_info['passing_veh_n_s'] + \
                                          traffic_light_info['passing_veh_e_w']

                    # Append date info to traffic light
                    traffic_light.append_date_contextual_info(date_info=date_info)

                    # Signal to publish the contextual information
                    traffic_light.publish_contextual_info()

                    # Reset contextual information
                    traffic_light.reset_contextual_info()

                # Create a dict with the summary information
                summary_info = {'waiting_time': summary_waiting_time, 'veh_passed': summary_veh_passed}

                # Process summary information
                traffic_info_payload = process_payload(traffic_info=summary_info, date_info=date_info)

                # Publish data
                self._mqtt_client.publish(topic=TRAFFIC_INFO_TOPIC,
                                          payload=parse_str_to_valid_schema(traffic_info_payload))

                # Reset counters
                summary_waiting_time, summary_veh_passed = 0, 0

            # Simulate a step
            self._traci.simulationStep()

            # Increase simulation step
            cur_timestep += 1

        # Close TraCI simulation, the adapters connection and the MQTT client
        self._traci.close()
        for traffic_light_id, traffic_light in traffic_lights.items():
            traffic_light.close_adapter_connection()
        self._mqtt_client.loop_stop()

    def apply_tl_programs(self, tl_programs: dict) -> None:
        """
        Apply a new program to each traffic light in the topology.

        :param tl_programs: new traffic light program per traffic light dict
        :type tl_programs: dict
        :return: None
        """
        for traffic_light, program in tl_programs.items():
            # Update program if it is not the same
            if self._traci.trafficlight.getProgram(traffic_light) != program:
                self._traci.trafficlight.setProgram(traffic_light, program)
