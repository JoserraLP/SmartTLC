import random
import subprocess

import pandas as pd

from sumo_generators.generators.flows_generator import FlowsGenerator
from sumo_generators.generators.sumo_config_generator import SumoConfigGenerator
from sumo_generators.network.grid.grid_net_generator import GridNetGenerator
from sumo_generators.network.net_topology import NetworkTopology
from sumo_generators.static.constants import *
from sumo_generators.time_patterns.time_patterns import TimePattern


def generate_network_file(rows: int = MIN_ROWS, cols: int = MIN_COLS, lanes: int = MIN_LANES, distance: int = DISTANCE,
                          junction: str = JUNCTION_TYPE, tl_type: str = TL_TYPE,
                          tl_layout: str = TL_LAYOUT, nodes_path: str = DEFAULT_NODES_DIR,
                          edges_path: str = DEFAULT_EDGES_DIR, network_path: str = DEFAULT_NET_DIR):
    """
    Creates the network generator and generates the output network file

    :param rows: number of rows of the matrix
    :type rows: int
    :param cols: number of cols of the matrix
    :type cols: int
    :param lanes: number of lanes per edge
    :type lanes: int
    :param distance: distance between nodes
    :type distance: float
    :param junction: junction type
    :type junction: str
    :param tl_type: traffic light type
    :type tl_type: str
    :param tl_layout: central nodes traffic light layout
    :type tl_layout: str
    :param nodes_path: directory where the nodes file will be generated
    :type nodes_path: str
    :param edges_path: directory where the edges file will be generated
    :type edges_path: str
    :param network_path: directory where the network file will be generated
    :type network_path: str
    :return: None
    """
    # Define the network generator
    net_generator = GridNetGenerator(rows=rows, cols=cols, lanes=lanes, distance=distance, junction=junction,
                                     tl_type=tl_type, tl_layout=tl_layout, nodes_path=nodes_path, edges_path=edges_path)

    # Generate the topology required files (nodes and edges)
    net_generator.generate_topology()

    params = ['netconvert', '-n', nodes_path, '-e', edges_path, '-o', network_path,
              '--tls.default-type', tl_type, '--no-turnarounds']

    # Create a subprocess in order to generate the network file using the previously generated files and the netconvert
    # command
    process = subprocess.Popen(params, stdout=subprocess.PIPE, universal_newlines=True)

    # Iterate until the process finishes, printing the command output
    while True:
        output = process.stdout.readline()
        print(output.strip())
        return_code = process.poll()
        if return_code is not None:
            # Process has finished, read rest of the output
            break


def generate_flow_file(flows_path: str, time_pattern_path: str = '', dates: str = '',
                       calendar_pattern_file: str = DEFAULT_TIME_PATTERN_FILE,
                       net_topology: NetworkTopology = None):
    """
    Generate the traffic flows based on the topology and store it on the output file.

    :param flows_path: flows file path.
    :type flows_path: str
    :param time_pattern_path: dataframe with the time pattern. Default is ''.
    :type time_pattern_path: pd.DataFrame
    :param dates: time pattern input file. Default is ''.
    :type dates: str
    :param calendar_pattern_file: Calendar time pattern file. Default is '../time_patterns/generated_calendar.csv'.
    :type calendar_pattern_file: str
    :param net_topology: network topology database connection
    :type net_topology: NetworkTopology
    :return: None
    """

    # Retrieve time pattern
    if time_pattern_path != '':
        # Retrieve time pattern file
        time_pattern = TimePattern(file_dir=time_pattern_path)
    elif dates != '':
        # Retrieve time pattern from given dates
        time_pattern = TimePattern(file_dir=calendar_pattern_file)
        start_date, end_date = dates.split('-')
        time_pattern.retrieve_pattern_days(start_date=start_date, end_date=end_date)
    else:
        # Initialize to None and exit
        time_pattern = None
        exit(-1)

    # Define flows generator
    flow_generator = FlowsGenerator()

    # Retrieve outers junctions from network database and its edges
    outer_junctions = net_topology.get_outer_junctions("inbound", edges=True)

    # Process to get only one instance of each source and target edge as the vehicles will reroute and its route will
    # change based on probabilities
    outer_junctions = pd.DataFrame(outer_junctions).drop_duplicates(subset=['from', 'to']) \
        .reset_index(drop=True).to_dict(orient='records')

    # Iter over the time pattern rows
    for index, row in enumerate(time_pattern.pattern.itertuples(index=False)):
        # Calculate flows values such as begin and end timesteps and its related traffic type
        begin = index * TIMESTEPS_PER_HOUR
        end = TIMESTEPS_PER_HOUR * (index + 1)
        # Index 1 is the traffic type
        traffic_type_name = list(FLOWS_VALUES.keys())[row[1]]

        # Generate the row traffic flow
        # Initialize the flows list
        flows = []

        # Retrieve lower and upper bound
        lower_bound = FLOWS_VALUES[traffic_type_name]['vehs_lower_limit']
        upper_bound = FLOWS_VALUES[traffic_type_name]['vehs_upper_limit']

        # Create a flow from each junction until next junction
        for outer_junction in outer_junctions:
            # Append flows file, where it is only used the "from" tag as the destination is unknown
            flows.append({'begin': begin, 'end': end,
                          'vehsPerHour': random.randint(lower_bound, upper_bound),
                          'from': outer_junction['from_edge']})

        # Add flows to the flows generator
        flow_generator.add_flows(flows)

    # Store the flows
    flow_generator.store_flows()
    # Store the flows file with the extension '.flows'
    flow_generator.write_output_file(flows_path+'.flows')
    # Clean flows from the generator
    flow_generator.clean_flows()


def generate_sumo_config_file(sumo_config_path: str, network_path: str):
    """
    Creates the SUMO configuration file

    :param sumo_config_path: directory where the SUMO configuration file will be generated
    :type sumo_config_path: str
    :param network_path: directory where the network file is stored
    :type network_path: str

    :return: None
    """

    # Define the generator
    sumo_config_generator = SumoConfigGenerator()

    # Define the input files removing the root folder
    input_files = {
        'net-file': network_path.split('/')[-1]
    }

    # Set input configuration files
    sumo_config_generator.set_input_files(input_files)

    # Define simulation begin time
    sumo_config_generator.set_begin_time(0)

    # Define the report policy
    policy = {'verbose': 'true', 'no-step-log': 'true'}

    # Set report policy
    sumo_config_generator.set_report_policy(policy)

    # Save the programs into an output file
    sumo_config_generator.write_output_file(sumo_config_path)
