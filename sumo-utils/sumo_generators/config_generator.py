import math
import os
import subprocess
import xml.etree.cElementTree as ET
from xml.dom import minidom

from sumo_generators.generators.sumo_config_generator import SumoConfigGenerator
from sumo_generators.network.net_generator import NetGenerator
from sumo_generators.static.argparse_types import *
from sumo_generators.static.constants import *


def generate_detector_file(network_path: str, detector_path: str, cols: int = MIN_COLS):
    """
    Updates the detector file to add the direction

    :param network_path: directory where the network file will be generated
    :type network_path: str
    :param detector_path: directory where the detector file will be generated
    :type detector_path: str
    :param cols: number of cols of the matrix
    :type cols: int
    """

    # Update cols value (subtract 2)
    cols -= 2

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
        from_node_letter, from_node_value, to_node_id, to_node_value = from_node[0], int(from_node[1:]), to_node[0], \
                                                                       int(to_node[1:])

        # Set direction to empty
        direction = ''
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


def generate_tll_file(network_path: str, tll_path: str, interval: int = -1,
                      proportion: bool = True):
    # Create root for tll
    tll_root = ET.Element("additional")

    # Define tl program id value
    tl_program_id = 1
    # Define tl program id schema
    tl_program_schema = 'static_program_{}'

    # Retrieve the XML content
    tree = ET.parse(network_path)
    # Get root
    root = tree.getroot()
    # Iterate over the traffic light programs
    for tl in root.iter(tag='tlLogic'):

        # Proportion traffic light phase duration
        if proportion:
            for i in range(0, len(TRAFFIC_PROPORTIONS)):
                # Retrieve the traffic light program info
                tl_dict = dict(tl.items())
                # Update the programID
                tl_dict['programID'] = tl_program_schema.format(i + 1)
                # Store the tl item
                tl_item = ET.SubElement(tll_root, 'tlLogic', attrib=tl_dict)
                # Retrieve the tl item phases
                tl_phases = [dict(tl_phase.items()) for tl_phase in list(tl.iter()) if tl_phase is not tl]

                # Calculate the time on EW direction by proportion
                time_ew = MAXIMUM_TIME_PHASE / (TRAFFIC_PROPORTIONS[i] + 1)

                for index, tl_phase in enumerate(tl_phases):
                    if index == 0:  # Green on NS
                        tl_phase['duration'] = str(math.floor(MAXIMUM_TIME_PHASE - time_ew))
                    elif index == 2:  # Green on EW
                        tl_phase['duration'] = str(math.ceil(time_ew))

                    ET.SubElement(tl_item, 'phase', attrib=tl_phase)

        # interval traffic light phase duration
        if interval:
            # Iterate over the number of intervals
            for i in range(0, int(MAXIMUM_TIME_BOUND_PHASE / interval) + 1):
                # Retrieve the traffic light program info
                tl_dict = dict(tl.items())
                # Update the programID
                tl_dict['programID'] = tl_program_schema.format(i + 1)
                # Store the tl item
                tl_item = ET.SubElement(tll_root, 'tlLogic', attrib=tl_dict)
                # Retrieve the tl item phases
                tl_phases = [dict(tl_phase.items()) for tl_phase in list(tl.iter()) if tl_phase is not tl]

                for index, tl_phase in enumerate(tl_phases):

                    if index == 0:  # Green on NS
                        tl_phase['duration'] = str(LOWER_BOUND_TIME_PHASE + i * interval)
                    elif index == 2:  # Green on EW
                        tl_phase['duration'] = str(UPPER_BOUND_TIME_PHASE - i * interval)

                    ET.SubElement(tl_item, 'phase', attrib=tl_phase)

    # Parse the XML object to be human-readable
    xmlstr = minidom.parseString(ET.tostring(tll_root)).toprettyxml(indent="   ")
    with open(tll_path, "w") as f:
        # Write into the file
        f.write(xmlstr)


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
    :return:
    """

    # Define the network generator
    net_generator = NetGenerator(rows=rows, cols=cols, lanes=lanes, distance=distance, junction=junction,
                                 tl_type=tl_type, tl_layout=tl_layout, nodes_path=nodes_path, edges_path=edges_path)

    # Generate the topology required files (nodes and edges)
    net_generator.generate_topology()

    # Create a subprocess in order to generate the network file using the previously generated files and the netconvert
    # command
    process = subprocess.Popen(
        ['netconvert', '-n', nodes_path, '-e', edges_path, '-o', network_path, '--tls.default-type', tl_type,
         '--no-turnarounds'],
        stdout=subprocess.PIPE,
        universal_newlines=True)

    # Iterate until the process finishes, printing the command output
    while True:
        output = process.stdout.readline()
        print(output.strip())
        return_code = process.poll()
        if return_code is not None:
            # Process has finished, read rest of the output
            break


def generate_sumo_config_file(sumo_config_path: str, network_path: str, tll_path: str, detector_path: str,
                              route_path: str = DEFAULT_ROUTE_DIR):
    # Define the generator
    sumo_config_generator = SumoConfigGenerator()

    # Define the input files removing the root folder
    input_files = {
        'net-file': network_path.replace(DEFAULT_DIR, ''),
        'route-files': route_path.replace(DEFAULT_DIR, ''),
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


def get_options():
    """
    Get options from the execution command

    :return: Arguments options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Script that generates a SUMO network file as a grid network '
                                                     'without the outer edges. NOTE: the dimensions of the grid are '
                                                     'defined +2 to the real number of edges in order to represent '
                                                     'a valid matrix. ')

    # Define generator groups

    # Output files group
    output_files_group = arg_parser.add_argument_group("Output configuration files generator",
                                                       description="Parameters related to the output "
                                                                   "configuration files")
    # Nodes file path
    output_files_group.add_argument("-n", "--nodes-path", dest="nodes_path", action="store", default=DEFAULT_NODES_DIR,
                                    type=str, help="define the path where the nodes file is created. "
                                                   f"Default is {DEFAULT_NODES_DIR}")

    # Edges file path
    output_files_group.add_argument("-e", "--edges-path", dest="edges_path", action="store", default=DEFAULT_EDGES_DIR,
                                    type=str, help=f"define the path where the edges file is created. "
                                                   f"Default is {DEFAULT_EDGES_DIR}")

    # Detector file path
    output_files_group.add_argument("-d", "--detector-path", dest="detector_path", action='store',
                                    default=DEFAULT_DET_DIR, type=str,
                                    help=f"detectors file location. Default is {DEFAULT_DET_DIR}")

    # TL programs file path
    output_files_group.add_argument("-t", "--tl-program-path", dest="tl_program_path", action='store',
                                    default=DEFAULT_TLL_DIR, type=str,
                                    help=f"SUMO traffic lights programs file location. Default is {DEFAULT_TLL_DIR}")

    # Full network file path
    output_files_group.add_argument("-o", "--output-network", dest="network_path", action="store",
                                    default=DEFAULT_NET_DIR, type=str,
                                    help=f"define the path where the network file is created."
                                         f"Default is {DEFAULT_NET_DIR}")

    # SUMO config file path
    output_files_group.add_argument("-s", "--sumo-config-path", dest="sumo_config_path", action='store',
                                    default=DEFAULT_CONFIG_DIR, type=str, help=f"SUMO configuration file location. "
                                                                               f"Default is {DEFAULT_CONFIG_DIR}")

    # Network Generator
    network_generator_group = arg_parser.add_argument_group("Network generator",
                                                            description="Parameters related to the network generation")
    network_generator_group.add_argument("-r", "--rows", dest="rows", action="store", default=MIN_ROWS,
                                         type=check_dimension, help=f"define the number of rows of the network. "
                                                                    f"Must be greater than 2. Default is {MIN_ROWS}")
    network_generator_group.add_argument("-c", "--cols", dest="cols", action="store", default=MIN_COLS,
                                         type=check_dimension, help=f"define the number of cols of the network. "
                                                                    f"Must be greater than 2. Default is {MIN_COLS}")
    network_generator_group.add_argument("-l", "--lanes", dest="lanes", action="store", default=MIN_LANES, type=int,
                                         help=f"define the number of lanes per edge. Must be greater than 0. "
                                              f"Default is {MIN_LANES}")
    network_generator_group.add_argument("--distance", dest="distance", action="store", default=DISTANCE, type=float,
                                         help=f"define the distance between the nodes. Must be greater than 0. "
                                              f"Default is {DISTANCE}")
    network_generator_group.add_argument("-j", "--junction", dest="junction", action="store", default=JUNCTION_TYPE,
                                         type=check_valid_junction_type,
                                         help="define the junction type on central nodes. Possible types are: priority,"
                                              " traffic_light, right_before_left, priority_stop, allway_stop, "
                                              f"traffic_light_right_on_red. Default is {JUNCTION_TYPE}.")
    # Next one is defined but overwritten by the generation of self traffic lights
    network_generator_group.add_argument("--tl-type", dest="tl_type", action="store", default=TL_TYPE,
                                         type=check_valid_tl_type, help="define the tl type, only if the 'junction' "
                                                                        "value is 'traffic_light'. Possible types are: "
                                                                        "static, actuated, delay_based. "
                                                                        f"Default is {TL_TYPE}.")
    network_generator_group.add_argument("--tl-layout", dest="tl_layout", action="store", default=TL_LAYOUT,
                                         type=check_valid_tl_layout,
                                         help="define the tl layout, only if the 'junction' value is 'traffic_light'. "
                                              "Possible types are: opposites, incoming, alternateOneWay. "
                                            f"Default is {TL_LAYOUT}.")

    # Traffic Light Program Generator
    tl_program_generator_group = arg_parser.add_argument_group("Traffic Light generator",
                                                               description="Parameters related to the Traffic Lights "
                                                                           "programs")

    tl_program_generator_group.add_argument("-i", "--interval", dest="interval", action='store', type=int,
                                            help="interval of seconds to be used in the traffic light generator")
    tl_program_generator_group.add_argument("-p", "--proportion", dest="proportion", action='store_true',
                                            default=True, help="flag to use proportions in the traffic light generator")

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == '__main__':
    # Retrieve execution options (parameters)
    exec_options = get_options()

    print(f"Executing network generator with parameters: {vars(exec_options)}")

    # Generate the network file
    generate_network_file(rows=exec_options.rows, cols=exec_options.cols, lanes=exec_options.lanes,
                          distance=exec_options.distance, junction=exec_options.junction,
                          tl_type=exec_options.tl_type, tl_layout=exec_options.tl_layout,
                          nodes_path=exec_options.nodes_path, edges_path=exec_options.edges_path,
                          network_path=exec_options.network_path)

    # Generate the detector file
    generate_detector_file(network_path=exec_options.network_path, detector_path=exec_options.detector_path,
                           cols=exec_options.cols)

    # Generate the traffic light programs file
    generate_tll_file(network_path=exec_options.network_path, tll_path=exec_options.tl_program_path,
                      proportion=exec_options.proportion, interval=exec_options.interval)

    # Generate the SUMO config file
    generate_sumo_config_file(sumo_config_path=exec_options.sumo_config_path, network_path=exec_options.network_path,
                              tll_path=exec_options.tl_program_path, detector_path=exec_options.detector_path)
