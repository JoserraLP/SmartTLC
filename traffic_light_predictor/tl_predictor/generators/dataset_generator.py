import random

from tl_predictor.generators.flows_generator import FlowsGenerator
from tl_predictor.static.constants import FLOWS_VALUES, FLOWS_OUTPUT_DIR
from tl_predictor.static.constants import TL_PROGRAMS, NUM_TRAFFIC_TYPES
from tl_predictor.storage.storage import Storage


class DatasetGenerator:
    """
    Dataset generator from the TraCI simulations
    """

    def __init__(self, sumo_conf, num_tl_programs: int = len(TL_PROGRAMS), num_traffic_types: int = NUM_TRAFFIC_TYPES):
        """
        DatasetGenerator initializer.

        :param sumo_conf: SUMO configuration
        :param num_tl_programs: number of traffic lights programs. Default is 4
        :type num_tl_programs: int
        :param num_traffic_types: number of traffic types. Default is 9
        :type num_traffic_types: int
        """

        # SUMO configuration files
        self._config_file = sumo_conf['config_file']
        self._sumo_binary = sumo_conf['sumo_binary']

        # Define the simulation storage
        self._storage = Storage()

        # Store parameters
        self._num_tl_programs = num_tl_programs
        self._num_traffic_types = num_traffic_types

        # Initialize TraCI simulation to none, to use it in different methods
        self._traci = None

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

    def simulate(self):
        """
        Perform the dataset generation with TraCI.

        :return: None
        """
        pass

    def store_all_data(self, output_file: str):
        """
        Store the dataset generated into a CSV file.

        :param output_file: directory where the dataset will be stored
        :type output_file: str
        :return: None
        """
        self._storage.to_csv(output_file)

    def select_traffic_type(self, sim_id: int):
        """
        Return the selected traffic type depending on the simulation number.
        Traffic types are:

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


        :param sim_id: simulation identifier
        :type sim_id: int
        :return: traffic type
        :rtype: int
        """
        # It is calculated by the module of the simulation id and the number of traffic types
        return sim_id % self._num_traffic_types

    def generate_traffic_flows(self, traffic_type: int, begin: int = 0, end: int = 500):
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
        :param end: end timestep per flow. Default is 500
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

        # Future works -> also generate random traffic that turns

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
