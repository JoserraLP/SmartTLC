import math
import os
import random
import subprocess
import xml.etree.cElementTree as ET
from xml.dom import minidom

import pandas as pd
from sumo_generators.generators.flows_generator import FlowsGenerator
from sumo_generators.generators.sumo_config_generator import SumoConfigGenerator
from sumo_generators.network.net_generator import NetGenerator
from sumo_generators.static.constants import *
from sumo_generators.time_patterns.time_patterns import TimePattern


def generate_detector_file(network_path: str, detector_path: str, cols: int = MIN_COLS):
    """
    Updates the detector file to add the direction of each detector

    :param network_path: directory where the network file is stored
    :type network_path: str
    :param detector_path: directory where the detector file will be generated
    :type detector_path: str
    :param cols: number of cols of the matrix
    :type cols: int
    :return: None
    """

    # Get SUMO environment variable
    sumo_env = os.getenv('SUMO_HOME')
    # Create a subprocess in order to generate the detector file based on the network topology
    process = subprocess.Popen(
        ['python', f'{sumo_env}/tools/output/generateTLSE1Detectors.py', '-n', network_path, '-d', str(DET_DISTANCE),
         '-f', str(DET_FREQ), '-o', detector_path, '-r', DET_FILE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        universal_newlines=True)

    # Iterate until the process finishes, not printing the command output
    while True:
        return_code = process.poll()
        if return_code is not None:
            # Process has finished, read rest of the output
            break

    # Retrieve the XML content
    tree = ET.parse(detector_path)
    # Get root
    root = tree.getroot()
    # Iterate over the detectors
    for detector in root:
        detector_dict = dict(detector.items())
        # Retrieve lanes
        _, from_node, to_node, lane_id = str(detector_dict['id']).split('_')
        # Retrieve node letter and value
        # Example is n_1 and e_1
        from_node_letter, from_node_value, to_node_id, to_node_value = from_node[0], int(from_node[1:]), to_node[0], \
                                                                       int(to_node[1:])

        # Set direction to empty
        direction = ''
        # Retrieve the detector direction on the outer edges
        if from_node_letter == 'n':
            direction = 'south'
        elif from_node_letter == 's':
            direction = 'north'
        elif from_node_letter == 'e':
            direction = 'west'
        elif from_node_letter == 'w':
            direction = 'east'
        else:
            # Both are center
            if from_node_value == to_node_value - cols:
                direction = 'north'
            elif from_node_value == to_node_value + cols:
                direction = 'south'
            elif from_node_value == to_node_value - 1:
                direction = 'west'
            elif from_node_value == to_node_value + 1:
                direction = 'east'

        # Update detector id
        detector.set('id', f'{direction}_{from_node}_{to_node}_{lane_id}')

    # Store the updated file
    tree.write(detector_path)


def generate_tl_file(network_path: str, tl_path: str, interval: int = -1, proportion: bool = True):
    """
    Creates the traffic light file based on the network topology and its type

    :param network_path: directory where the network file is stored
    :type network_path: str
    :param tl_path: directory where the tll file will be generated
    :type tl_path: str
    :param interval: interval between TL phases. Default to -1 which means it is not used.
    :type interval: int
    :param proportion: flag enabling proportion-based TL programs. Default to True.
    :type proportion: bool
    :return: None
    """

    # Create root for tll
    tl_root = ET.Element("additional")

    # Define tl program id schema
    tl_program_schema = 'static_program_{}'

    # Retrieve the XML content
    tree = ET.parse(network_path)
    # Get root
    root = tree.getroot()
    # Iterate over the traffic light programs
    for tl in root.iter(tag='tlLogic'):
        # Initialize number of programs to 0
        num_programs = 0
        # Calculate number of programs based on proportion or interval traffic light types
        if proportion:
            num_programs = len(TRAFFIC_PROPORTIONS)
        elif interval:
            num_programs = int(MAXIMUM_TIME_BOUND_PHASE / interval) + 1

        # Iterate over the number of traffic programs
        for i in range(0, num_programs):
            # Retrieve the traffic light program info
            tl_dict = dict(tl.items())
            # Update the programID
            tl_dict['programID'] = tl_program_schema.format(i + 1)
            # Store the tl item
            tl_item = ET.SubElement(tl_root, 'tlLogic', attrib=tl_dict)
            # Retrieve the tl item phases
            tl_phases = [dict(tl_phase.items()) for tl_phase in list(tl.iter()) if tl_phase is not tl]

            # Calculate the time on EW direction by proportion (used on proportion type)
            time_ew = MAXIMUM_TIME_PHASE / (TRAFFIC_PROPORTIONS[i] + 1)

            for index, tl_phase in enumerate(tl_phases):
                # Update the green phases
                if index == 0:  # Green on NS
                    tl_phase['duration'] = str(LOWER_BOUND_TIME_PHASE + i * interval) if interval \
                        else str(math.floor(MAXIMUM_TIME_PHASE - time_ew))
                elif index == 2:  # Green on EW
                    tl_phase['duration'] = str(UPPER_BOUND_TIME_PHASE - i * interval) if interval \
                        else str(math.ceil(time_ew))
                # Add the traffic light phase
                ET.SubElement(tl_item, 'phase', attrib=tl_phase)

    # Parse the XML object to be human-readable
    xmlstr = minidom.parseString(ET.tostring(tl_root)).toprettyxml(indent="   ")
    with open(tl_path, "w") as f:
        # Write into the file
        f.write(xmlstr)


def generate_network_file(rows: int = MIN_ROWS, cols: int = MIN_COLS, lanes: int = MIN_LANES, distance: int = DISTANCE,
                          junction: str = JUNCTION_TYPE, tl_type: str = TL_TYPE,
                          tl_layout: str = TL_LAYOUT, nodes_path: str = DEFAULT_NODES_DIR,
                          edges_path: str = DEFAULT_EDGES_DIR, network_path: str = DEFAULT_NET_DIR,
                          allow_add_left_phases: bool = ALLOW_ADD_LEFT_PHASES):
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
    :param allow_add_left_phases: flag to allow additional traffic lights left turn phases
    :type allow_add_left_phases: bool
    :return:
    """
    # Define the network generator
    net_generator = NetGenerator(rows=rows, cols=cols, lanes=lanes, distance=distance, junction=junction,
                                 tl_type=tl_type, tl_layout=tl_layout, nodes_path=nodes_path, edges_path=edges_path)

    # Generate the topology required files (nodes and edges)
    net_generator.generate_topology()

    params = ['netconvert', '-n', nodes_path, '-e', edges_path, '-o', network_path,
              '--tls.default-type', tl_type, '--no-turnarounds']
    # Add additional params
    if not allow_add_left_phases:
        params.extend(['--tls.left-green.time', str(0)])

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


def generate_flow_file(flows_path: str, rows: int, cols: int, time_pattern_path: str = '', dates: str = '',
                       calendar_pattern_file: str = DEFAULT_TIME_PATTERN_FILE):
    """
    Generate the traffic flows and store it on the output file.

    Traffic_type: \n
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

    :param flows_path: flows file path.
    :type flows_path: str
    :param rows: number of rows of the matrix
    :type rows: int
    :param cols: number of cols of the matrix
    :type cols: int
    :param time_pattern_path: dataframe with the time pattern. Default is ''.
    :type time_pattern_path: pd.DataFrame
    :param dates: time pattern input file. Default is ''.
    :type dates: str
    :param calendar_pattern_file: Calendar time pattern file. Default is '../time_patterns/generated_calendar.csv'.
    :type calendar_pattern_file: str
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

    # Iter over the time pattern rows
    for index, row in time_pattern.pattern.iterrows():
        # Calculate flows values such as begin and end timesteps and its related traffic type
        begin = index * TIMESTEPS_PER_HALF_HOUR
        end = TIMESTEPS_PER_HALF_HOUR * (index + 1)
        traffic_type = row['traffic_type']

        # Generate the row traffic flow
        # Initialize the flows list
        flows = []

        # The traffic generated will be bidirectionally
        ns_traffic_type, ew_traffic_type = TRAFFIC_TYPE_RELATION[traffic_type]

        # Create NS traffic
        # Retrieve lower and upper bound
        lower_bound = FLOWS_VALUES[ns_traffic_type]['vehsPerHour'] - FLOWS_VALUES[ns_traffic_type]['vehs_range']
        upper_bound = FLOWS_VALUES[ns_traffic_type]['vehsPerHour'] + FLOWS_VALUES[ns_traffic_type]['vehs_range']

        # From external to center
        flows.extend([
            {'begin': begin, 'end': end,
             'vehsPerHour': random.randint(lower_bound, upper_bound),
             'from': f'n{i}_c{i}', 'to': f'c{cols * (rows - 1) + i}_s{i}'} for i in range(1, cols + 1)])

        # From center to external
        flows.extend([
            {'begin': begin, 'end': end,
             'vehsPerHour': random.randint(lower_bound, upper_bound),
             'from': f's{i}_c{cols * (rows - 1) + i}', 'to': f'c{i}_n{i}'} for i in range(1, cols + 1)])

        # Create EW traffic
        # Retrieve lower and upper bound
        lower_bound = FLOWS_VALUES[ew_traffic_type]['vehsPerHour'] - FLOWS_VALUES[ew_traffic_type]['vehs_range']
        upper_bound = FLOWS_VALUES[ew_traffic_type]['vehsPerHour'] + FLOWS_VALUES[ew_traffic_type]['vehs_range']

        # From external to center
        flows.extend([
            {'begin': begin, 'end': end,
             'vehsPerHour': random.randint(lower_bound, upper_bound),
             'from': f'w{i}_c{(i - 1) * cols + 1}', 'to': f'c{cols * i}_e{i}'}
            for i in range(1, rows + 1)])

        # From center to external
        flows.extend([
            {'begin': begin, 'end': end,
             'vehsPerHour': random.randint(lower_bound, upper_bound),
             'from': f'e{i}_c{cols * i}', 'to': f'c{(i - 1) * cols + 1}_w{i}'}
            for i in range(1, rows + 1)])

        # Add flows to the flows generator
        flow_generator.add_flows(flows)

    # Store the flows
    flow_generator.store_flows()
    # Store the flows file at a given position
    flow_generator.write_output_file(flows_path)
    # Clean flows from the generator
    flow_generator.clean_flows()


def generate_sumo_config_file(sumo_config_path: str, network_path: str, tll_path: str, detector_path: str):
    """
    Creates the SUMO configuration file

    :param sumo_config_path: directory where the SUMO configuration file will be generated
    :type sumo_config_path: str
    :param network_path: directory where the network file is stored
    :type network_path: str
    :param tll_path: directory where the tll file is stored
    :type tll_path: str
    :param detector_path: directory where the detector file is stored
    :type detector_path: str
    :return: None
    """

    # Define the generator
    sumo_config_generator = SumoConfigGenerator()

    # Define the input files removing the root folder
    input_files = {
        'net-file': network_path.replace(DEFAULT_DIR, ''),
        'additional-files': tll_path.replace(DEFAULT_DIR, '') + "," + detector_path.replace(DEFAULT_DIR, '')
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
