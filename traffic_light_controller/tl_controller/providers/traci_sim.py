import paho.mqtt.client as mqtt
import traci
from sumo_generators.network.topology.net_matrix import NetMatrix
from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, TRAFFIC_INFO_TOPIC, TIMESTEPS_TO_STORE_INFO
from sumo_generators.time_patterns.time_patterns import TimePattern
from sumo_generators.time_patterns.utils import retrieve_date_info
from sumo_generators.utils.utils import parse_str_to_valid_schema
from tl_controller.adaptation.context import TrafficLightAdapter
from tl_controller.adaptation.strategy import *
from tl_controller.providers.utils import *
from tl_controller.static.constants import *
from turns_predictor.providers.predictor import TurnPredictor


class TraCISimulator:
    """
    Traffic Light Controller class
    """

    def __init__(self, sumo_conf, turn_pattern_file: str, time_pattern_file: str = '', dates: str = '',
                 mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT, local: bool = False):
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
        :param local: flag to execute locally the component. It will not connect to the middleware.
        :type local: bool
        """

        # Define time pattern
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
        self._config_file, self._sumo_binary = sumo_conf['config_file'], sumo_conf['sumo_binary']

        # Initialize TraCI simulation, topology info, traffic lights and date info to None
        self._traci, self._topology_rows, self._topology_cols, self._net_topology, self._traffic_lights = None, None, \
                                                                                                          None, None, \
                                                                                                          None
        # TL program to the middle one
        self._tl_program = TL_PROGRAMS[int(len(TL_PROGRAMS) / 2)]

        # Store local flag
        self._local = local

        # Initialize current simulation step and temporal window
        self._cur_timestep, self._temporal_window = 0, 0

        # Initialize date info
        self._date_info = retrieve_date_info(timestep=0, time_pattern=self._time_pattern)

        # Execute locally
        if local:
            self._mqtt_client = None
        # Connect to middleware
        else:
            # Create the MQTT client, its callbacks and its connection to the broker
            self._mqtt_client = mqtt.Client()
            self._mqtt_client.connect(mqtt_url, mqtt_port)
            self._mqtt_url = mqtt_url
            self._mqtt_port = mqtt_port
            self._mqtt_client.loop_start()

    def retrieve_simulation_params(self, load_vehicles_dir: str = '') -> list:
        """
        Retrieve the simulation params

        :param load_vehicles_dir: directory to load the vehicles flows.
        :type load_vehicles_dir: str

        :return: simulation parameters
        :rtype: list
        """
        # Load vehicles info
        if load_vehicles_dir:
            add_params = ["--route-files", load_vehicles_dir]
        else:
            add_params = ["--route-files", FLOWS_OUTPUT_DIR]

        # Retrieve base params
        sumo_params = [self._sumo_binary, "-c", self._config_file, "--no-warnings"]

        # Extend with additional ones
        sumo_params.extend(add_params)

        return sumo_params

    def install_traffic_component(self, components: dict) -> None:
        """
        Install different components inside the traffic lights specified by parameters.

        :param components: component to enable, along with its type.
        :type components: dict
        :return: None
        """
        # Iterate over the components
        for component_type, component in components.items():
            # Start the components in the specified traffic lights
            if component == 'all':
                component_traffic_lights = [v for k, v in self._traffic_lights.items()]
            elif component:
                if ',' in component:
                    # Retrieve those traffic lights specified
                    component_traffic_lights = [v for k, v in self._traffic_lights.items() if k in component.split(',')]
                else:
                    # Single one traffic light
                    component_traffic_lights = [self._traffic_lights[component]]
            else:
                # Empty
                component_traffic_lights = []

            # Iterate over the traffic lights components
            for traffic_light in component_traffic_lights:
                if component_type == 'traffic_analyzer':
                    # Initialize empty to deploy locally
                    traffic_light.enable_traffic_analyzer(traffic_analyzer=TrafficAnalyzer(mqtt_url='', mqtt_port=0))
                elif component_type == 'turn_predictor':
                    # Initialize empty to deploy locally
                    traffic_light.enable_turn_predictor(
                        turn_predictor=TurnPredictor(mqtt_url='', mqtt_port=0,
                                                     model_base_dir=TURN_PREDICTOR_MODEL_BASE_DIR,
                                                     parsed_values_file=TURN_PREDICTOR_PARSED_VALUES_FILE,
                                                     performance_file=TURN_PREDICTOR_PERFORMANCE_FILE))
                elif 'traffic_predictor' in component_type:
                    # Retrieve type of traffic predictor
                    _, traffic_predictor_type = component_type.split(':')
                    # Get flag related to the predictor type
                    date = True if traffic_predictor_type == 'date' else False

                    # Initialize empty to deploy locally
                    traffic_light.enable_traffic_predictor(
                        traffic_predictor=TrafficPredictor(date=date, mqtt_url='', mqtt_port=0,
                                                           model_base_dir=TRAFFIC_PREDICTOR_MODEL_BASE_DIR.format(
                                                               traffic_predictor_type),
                                                           parsed_values_file=TRAFFIC_PREDICTOR_PARSED_VALUES_FILE,
                                                           performance_file=TRAFFIC_PREDICTOR_PERFORMANCE_FILE.format(
                                                               traffic_predictor_type)))

    def initialize_simulation_topology(self, simulation_params: list, traffic_analyzer: str = '',
                                       turn_predictor: str = '', traffic_predictor: str = '',
                                       traffic_predictor_type: str = '') -> None:
        """
        Initialize simulation topology network

        :param simulation_params: simulation parameters.
        :type simulation_params: list
        :param traffic_analyzer: enables analyzer on the specified traffic lights.
        :type traffic_analyzer: str
        :param turn_predictor: enables turn predictor on the specified traffic lights.
        :type turn_predictor: str
        :param traffic_predictor: enables traffic predictor on the specified traffic lights.
        :type traffic_predictor: str
        :param traffic_predictor_type: specify the traffic predictor type. Options are: 'date' or 'contextual'
        :type traffic_predictor_type: str
        :return: None
        """
        # SUMO is started as a subprocess and then the python script connects and runs.
        traci.start(simulation_params)

        # Store traci instance into the class
        self._traci = traci

        # Load TL programs
        for traffic_light in self._traci.trafficlight.getIDList():
            self._traci.trafficlight.setProgram(traffic_light, self._tl_program)

        # Retrieve network topology
        self._topology_rows, self._topology_cols = get_topology_dim(self._traci)

        # Retrieve all edges
        edges = [edge for edge in self._traci.edge.getIDList() if ':' not in edge]

        # Define and generate the network topology
        self._net_topology = NetMatrix(num_rows=self._topology_rows, num_cols=self._topology_cols,
                                       valid_edges=edges, traci=self._traci)
        self._net_topology.generate_network()

        # Initialize Traffic Lights with the static adaptation strategy by default
        self._traffic_lights = {traffic_light: TrafficLightAdapter(id=traffic_light, traci=traci, local=self._local,
                                                                   adaptation_strategy=StaticAS(traffic_light),
                                                                   net_topology=self._net_topology,
                                                                   mqtt_url=self._mqtt_url, mqtt_port=self._mqtt_port,
                                                                   rows=self._topology_rows,
                                                                   cols=self._topology_cols)
                                for traffic_light in self._traci.trafficlight.getIDList()}

        # "install" traffic analyzers, traffic and turn predictors on all the traffic lights
        # The traffic predictor also specifies the type of predictor using :
        components = {'traffic_analyzer': traffic_analyzer, 'turn_predictor': turn_predictor,
                      'traffic_predictor:' + traffic_predictor_type: traffic_predictor}
        self.install_traffic_component(components=components)

        # Initialize date info on each traffic light
        for traffic_light_id, traffic_light in self._traffic_lights.items():
            # Store date info and temporal window
            traffic_light.insert_date_info(temporal_window=self._temporal_window, date_info=self._date_info)

    def monitor_adapt_traffic_lights(self) -> None:
        """
        Update the traffic light program and monitor the contextual information

        :return: None
        """
        # Here the global controller signalises the traffic lights to perform different actions
        # Signal each traffic light to perform its own adaptation process
        for traffic_light_id, traffic_light in self._traffic_lights.items():

            # If the temporal window is finished
            # TODO ask cristina if we adapt each traffic light cycle or per time window of 5 minutes
            if self._cur_timestep % TIMESTEPS_TO_STORE_INFO == 0:
                # Update the traffic light program based on the adapter
                traffic_light.update_tl_program(timestep=self._cur_timestep)

            # Remove previous passing vehicles
            traffic_light.remove_passing_vehicles()

            # Count number of vehicles passing
            traffic_light.count_passing_vehicles()

            # Update waiting time per lane on each junction
            traffic_light.calculate_waiting_time_per_lane(cols=self._topology_cols)

    def calculate_turns(self, load_vehicles_dir: str = '') -> None:
        """
        Calculate the turns if enabled based on the actual timestamp

        :param load_vehicles_dir: directory to load the vehicles flows.
        :type load_vehicles_dir: str
        :return: None
        """

        # If vehicles are not loaded means that they need to calculate the new route based on the turn pattern
        if not load_vehicles_dir and self._turn_pattern:
            # Retrieve turn probabilities by edges
            turn_prob_by_edges = retrieve_turn_prob_by_edge(traci=traci,
                                                            turn_prob=self._turn_pattern.retrieve_turn_prob(
                                                                simulation_timestep=self._cur_timestep))

            # Update current vehicles routes to enable turns, using the network topology
            # Insert the traffic info to store the number of turning vehicles
            self._net_topology.update_route_with_turns(traffic_lights=self._traffic_lights,
                                                       turn_prob_by_edges=turn_prob_by_edges)

        else:
            # Otherwise calculate the number of turning vehicles as they are loaded, using the network topology
            self._net_topology.calculate_turning_vehicles(traffic_lights=self._traffic_lights)

    def process_publish_traffic_information(self, summary_waiting_time: int, summary_veh_passed: int,
                                            date_info: dict) -> None:
        """
        Gather all the information related to the traffic lights, add it to the summary variables and publish them.

        :param summary_waiting_time: summary waiting time of the temporal window
        :type summary_waiting_time: int
        :param summary_veh_passed: summary of vehicles passed on the temporal window
        :type summary_veh_passed: int
        :param date_info: date information
        :type date_info: dict
        :return: None
        """
        # Iterate over each traffic light, retrieve its information using the current timestamp and signalize to
        # publish them
        for traffic_light_id, traffic_light in self._traffic_lights.items():
            # Retrieve traffic light information
            traffic_light_info = traffic_light.get_traffic_info_by_temporal_window(self._temporal_window)

            # Store summary of waiting time and vehicles passed
            summary_waiting_time += traffic_light_info['waiting_time_veh_n_s'] + traffic_light_info[
                'waiting_time_veh_e_w']
            summary_veh_passed += traffic_light_info['passing_veh_n_s'] + traffic_light_info['passing_veh_e_w']

            # Append date information
            traffic_light.insert_date_info(temporal_window=self._temporal_window, date_info=date_info)

            # Publish the contextual information
            traffic_light.publish_contextual_info()

            # Next components has the inner check if is available

            # Publish traffic analyzer information
            traffic_light.publish_analyzer_info()

            # Publish turn predictors information
            traffic_light.publish_turn_predictions()

            # Publish traffic type predictors information
            traffic_light.publish_traffic_type_prediction()

    def simulate(self, load_vehicles_dir: str = ''):
        """
        Perform the simulations by a time pattern with TraCI.

        :param load_vehicles_dir: directory to load the vehicles flows.
        :type load_vehicles_dir: str
        :return: None
        """

        """ Initialize the simulation variables """
        # Define initial timestep and maximum timesteps
        self._cur_timestep, max_timesteps = 0, len(self._time_pattern.pattern) * TIMESTEPS_PER_HALF_HOUR

        # Append traffic global information
        summary_waiting_time, summary_veh_passed = 0, 0

        # Traci simulation. Iterate until simulation is ended
        while self._cur_timestep < max_timesteps:

            # Update and monitor the traffic light behavior
            self.monitor_adapt_traffic_lights()

            # Calculate vehicle turns
            self.calculate_turns(load_vehicles_dir=load_vehicles_dir)

            # Store info each time interval
            if self._cur_timestep % TIMESTEPS_TO_STORE_INFO == 0:

                # Publish the information
                if not self._local:
                    # Gather all the traffic lights information and publish them
                    self.process_publish_traffic_information(summary_waiting_time=summary_waiting_time,
                                                             summary_veh_passed=summary_veh_passed,
                                                             date_info=self._date_info)

                    # Create a dict with the summary information
                    summary_info = {'waiting_time': summary_waiting_time, 'veh_passed': summary_veh_passed}

                    # Process summary information
                    traffic_info_payload = process_payload(traffic_info=summary_info, date_info=self._date_info)

                    # Publish data
                    self._mqtt_client.publish(topic=TRAFFIC_INFO_TOPIC,
                                              payload=parse_str_to_valid_schema(traffic_info_payload))

                    # Reset counters
                    summary_waiting_time, summary_veh_passed = 0, 0

                # Increase the temporal window
                self._temporal_window += 1

                # Calculate new date info
                self._date_info = retrieve_date_info(timestep=self._cur_timestep, time_pattern=self._time_pattern)

                # Update new date to the traffic lights and store new temporal window
                for traffic_light_id, traffic_light in self._traffic_lights.items():
                    # Create new historical traffic info
                    traffic_light.create_historical_traffic_info(temporal_window=self._temporal_window)

                    # Insert date info and temporal window
                    traffic_light.insert_date_info(temporal_window=self._temporal_window, date_info=self._date_info)

            # Simulate a step
            self._traci.simulationStep()

            # Increase simulation step
            self._cur_timestep += 1

        # Close TraCI simulation, the adapters connection and the MQTT client
        self._traci.close()
        # If it is deployed
        if not self._local:
            for traffic_light_id, traffic_light in self._traffic_lights.items():
                traffic_light.close_connection()
            self._mqtt_client.loop_stop()
