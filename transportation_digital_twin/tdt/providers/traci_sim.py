import paho.mqtt.client as mqtt
import traci

from sumo_generators.network.net_topology import NetworkTopology
from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, TRAFFIC_INFO_TOPIC, DEFAULT_TEMPORAL_WINDOW, \
    POSSIBLE_CYCLES
from sumo_generators.time_patterns.time_patterns import TimePattern
from sumo_generators.time_patterns.utils import retrieve_date_info
from sumo_generators.utils.utils import parse_to_valid_schema
from tdt.adaptation.context import TrafficLightAdapter
from tdt.adaptation.strategy import *
from tdt.providers.utils import *
from tdt.static.constants import *
from turns_predictor.providers.predictor import TurnPredictor


class TraCISimulator:
    """
    Traffic Light Controller class
    """

    def __init__(self, sumo_conf, time_pattern_file: str = '', dates: str = '',
                 mqtt_url: str = MQTT_URL, mqtt_port: int = MQTT_PORT, local: bool = False,
                 temporal_window: int = DEFAULT_TEMPORAL_WINDOW):
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
        :param local: flag to execute locally the component. It will not connect to the middleware.
        :type local: bool
        :param temporal_window: number of TL cycles to gather information.
        :type temporal_window: int
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

        # SUMO configuration files
        self._config_file, self._sumo_binary = sumo_conf['config_file'], sumo_conf['sumo_binary']

        # Define temporal window based on number of cycles, currently all the TLs has a cycle of 90 seconds (urban)
        self._timesteps_monitor_info = POSSIBLE_CYCLES['urban'] * temporal_window

        # Initialize TraCI simulation, topology info, traffic lights and date info to None
        self._traci, self._net_topology, self._traffic_lights = None, None, None

        # TL program to the middle one
        # self._tl_program = TL_PROGRAMS[int(len(TL_PROGRAMS) / 2)]
        # TL program to '0'
        self._tl_program = '0'

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

            # TODO define also the adaptation strategies, now there are "installed" the individual ones but in the
            #  future this would change in real-time and used at the same time for example the analyzer and the
            #  traffic predictor

            # Iterate over the traffic lights components
            for traffic_light in component_traffic_lights:
                if component_type == 'traffic_analyzer':
                    # Create with empty values to deploy locally
                    traffic_analyzer = TrafficAnalyzer(mqtt_url='', mqtt_port=0)
                    # Enable traffic analyzer
                    traffic_light.enable_traffic_analyzer(traffic_analyzer=traffic_analyzer)

                    # Start the basic adaptation strategy
                    traffic_light.adaptation_strategy = SelfTrafficAnalyzerAS(analyzer=traffic_analyzer,
                                                                              traffic_light_id=traffic_light.tl_id)
                elif component_type == 'turn_predictor':
                    # Initialize empty to deploy locally
                    traffic_light.enable_turn_predictor(
                        turn_predictor=TurnPredictor(mqtt_url='', mqtt_port=0,
                                                     model_base_dir=TURN_PREDICTOR_MODEL_BASE_DIR,
                                                     parsed_values_file=TURN_PREDICTOR_PARSED_VALUES_FILE,
                                                     performance_file=TURN_PREDICTOR_PERFORMANCE_FILE))
                elif 'traffic_predictor' in component_type:
                    # Initialize empty to deploy locally
                    traffic_predictor = TrafficPredictor(mqtt_url='', mqtt_port=0,
                                                         model_base_dir=TRAFFIC_PREDICTOR_MODEL_BASE_DIR,
                                                         parsed_values_file=TRAFFIC_PREDICTOR_PARSED_VALUES_FILE,
                                                         performance_file=TRAFFIC_PREDICTOR_PERFORMANCE_FILE)
                    # Enable traffic predictor
                    traffic_light.enable_traffic_predictor(traffic_predictor=traffic_predictor)

                    # Start the basic adaptation strategy
                    traffic_light.adaptation_strategy = SelfTrafficPredictorAS(traffic_predictor=traffic_predictor,
                                                                               traffic_light_id=traffic_light.tl_id)

    def initialize_simulation_topology(self, simulation_params: list, topology_database_params: dict,
                                       traffic_analyzer: str = '', turn_predictor: str = '',
                                       traffic_predictor: str = '') -> None:
        """
        Initialize simulation topology network

        :param simulation_params: simulation parameters.
        :type simulation_params: list
        :param topology_database_params: topology database connection parameters.
        :type topology_database_params: dict
        :param traffic_analyzer: enables analyzer on the specified traffic lights.
        :type traffic_analyzer: str
        :param turn_predictor: enables turn predictor on the specified traffic lights.
        :type turn_predictor: str
        :param traffic_predictor: enables traffic predictor on the specified traffic lights.
        :type traffic_predictor: str
        :return: None
        """
        # SUMO is started as a subprocess and then the python script connects and runs.
        traci.start(simulation_params)

        # Store traci instance into the class
        self._traci = traci

        # Create Network Topology and connection to database
        self._net_topology = NetworkTopology(ip_address=topology_database_params['ip_address'],
                                             password=topology_database_params['password'],
                                             user=topology_database_params['user'], traci=self._traci)

        # Get traffic light names from database
        traffic_lights_names = traci.trafficlight.getIDList()

        # Load TL programs
        for traffic_light in traffic_lights_names:
            self._traci.trafficlight.setProgram(traffic_light, self._tl_program)

        # Initialize Traffic Lights with the static adaptation strategy by default
        self._traffic_lights = {traffic_light: TrafficLightAdapter(tl_id=traffic_light, traci=traci, local=self._local,
                                                                   adaptation_strategy=StaticAS(traffic_light),
                                                                   net_topology=self._net_topology,
                                                                   mqtt_url=self._mqtt_url, mqtt_port=self._mqtt_port)
                                for traffic_light in traffic_lights_names}

        # "install" traffic analyzers, traffic and turn predictors on all the traffic lights
        components = {'traffic_analyzer': traffic_analyzer, 'turn_predictor': turn_predictor,
                      'traffic_predictor': traffic_predictor}

        self.install_traffic_component(components=components)

        # Initialize date info on each traffic light
        for traffic_light_id, traffic_light in self._traffic_lights.items():
            # Get actual program
            actual_program = traffic_light.get_tl_program()

            # Create new historical traffic info
            traffic_light.create_historical_traffic_info(temporal_window=self._temporal_window,
                                                         actual_program=actual_program)

            # Store date info and temporal window
            traffic_light.insert_date_info(temporal_window=self._temporal_window, date_info=self._date_info)

    def adapt_traffic_lights(self) -> None:
        """
        Adapt and update traffic lights program based on contextual information

        :return: None
        """
        # Global controller signalises the traffic lights to perform  its own adaptation process
        for traffic_light_id, traffic_light in self._traffic_lights.items():
            # Update the traffic light program based on the adapter
            traffic_light.update_tl_program(timestep=self._cur_timestep)

    def monitor_traffic_lights(self) -> None:
        """
        Monitor traffic light contextual information

        :return: None
        """
        # Monitor traffic lights contextual information
        for traffic_light_id, traffic_light in self._traffic_lights.items():
            # Remove previous passing vehicles
            traffic_light.remove_passing_vehicles()

            # Count number of vehicles passing
            traffic_light.count_passing_vehicles()

            # Update waiting time per lane on each junction
            traffic_light.calculate_waiting_time_per_lane()

            # Calculate emissions per lane on each junction
            traffic_light.calculate_emissions_per_lane()

    def process_publish_traffic_information(self) -> None:
        """
        Gather all the information related to the traffic lights and publish them.

        :return: None
        """
        # Initialize summary variables
        summary_waiting_time, summary_veh_passed = 0, 0
        # Iterate over each traffic light, retrieve its information using the current timestamp and signalize to
        # publish them
        for traffic_light_id, traffic_light in self._traffic_lights.items():
            # Retrieve traffic light information
            traffic_light_info = traffic_light.get_traffic_info_by_temporal_window(self._temporal_window)

            # Store summary of waiting time and vehicles passed
            summary_waiting_time += sum([v['waiting_time_veh'] for k, v in
                                         traffic_light_info['contextual_info'].items()])

            summary_veh_passed += sum([v['num_passing_veh'] for k, v in
                                       traffic_light_info['contextual_info'].items()])

            # Append date information
            traffic_light.insert_date_info(temporal_window=self._temporal_window, date_info=self._date_info)

            # Retrieve contextual info
            contextual_tl_info = traffic_light.get_processed_contextual_info()

            # Store traffic light lanes contextual into the net topology database
            self._net_topology.update_lanes_info(traffic_light_id, contextual_lane_info=contextual_tl_info['info'])

            # Store traffic light program info
            self._net_topology.update_traffic_light_program(tl_id=traffic_light_id,
                                                            tl_program=traffic_light.get_tl_program())

            # Publish the contextual information
            traffic_light.publish_contextual_info(contextual_tl_info=contextual_tl_info)

            # Next components have the inner check if is available

            # Publish traffic analyzer information
            traffic_light.publish_analyzer_info()

            # Publish turn predictors information
            traffic_light.publish_turn_predictions()

            # Publish traffic type predictors information
            traffic_light.publish_traffic_type_prediction()

        # Process summary information
        traffic_info_payload = process_payload(traffic_info={'waiting_time': summary_waiting_time,
                                                             'veh_passed': summary_veh_passed},
                                               date_info=self._date_info)

        # Publish data
        self._mqtt_client.publish(topic=TRAFFIC_INFO_TOPIC,
                                  payload=parse_to_valid_schema(traffic_info_payload))

    def clean_traffic_lights(self) -> None:
        """
        Clean and initialize traffic lights info such as date info and create new instance of historical info

        :return: None
        """
        # Update new date to the traffic lights, store new temporal window and road related info into the net db
        for traffic_light_id, traffic_light in self._traffic_lights.items():
            # Increase temporal window
            traffic_light.increase_temporal_window()

            # Get actual program
            actual_program = traffic_light.get_tl_program()

            # Create new historical traffic info
            traffic_light.create_historical_traffic_info(temporal_window=self._temporal_window,
                                                         actual_program=actual_program)

            # Insert date info and temporal window
            traffic_light.insert_date_info(temporal_window=self._temporal_window, date_info=self._date_info)

    def simulate(self):
        """
        Perform the simulations by a time pattern with TraCI.

        :return: None
        """

        """ Initialize the simulation variables """
        # Define initial timestep and maximum timestep
        self._cur_timestep, max_timestep = 0, len(self._time_pattern.pattern) * TIMESTEPS_PER_HOUR

        # Traci simulation. Iterate until simulation is ended
        while self._cur_timestep < max_timestep:

            # Monitor the traffic light contextual information
            self.monitor_traffic_lights()

            # Store info each time interval
            if self._cur_timestep % self._timesteps_monitor_info == 0:

                # Adapt traffic light programs
                self.adapt_traffic_lights()

                # Publish the information
                if not self._local:
                    # Gather all the traffic lights information and publish them, along with its summary info
                    self.process_publish_traffic_information()

                # Increase the temporal window
                self._temporal_window += 1

                # Calculate new date info
                self._date_info = retrieve_date_info(timestep=self._cur_timestep, time_pattern=self._time_pattern)

                # Clean traffic lights info
                self.clean_traffic_lights()

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
