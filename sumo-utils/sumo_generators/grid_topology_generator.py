from sumo_generators.generators.utils import generate_network_file, \
    generate_sumo_config_file
from sumo_generators.static.argparse_types import *
from sumo_generators.static.constants import *


def get_options():
    """
    Get options from the execution command

    :return: Arguments options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Script that generates a SUMO network file as a grid network '
                                                     'without the outer edges.')

    # Define generator groups

    # Output files group
    output_files_group = arg_parser.add_argument_group("Output configuration files generator",
                                                       description="Parameters related to the output "
                                                                   "configuration files")
    # Nodes file path
    output_files_group.add_argument("-n", "--nodes-path", dest="nodes_path", action="store", default=DEFAULT_NODES_DIR,
                                    type=str, help="path where the nodes file is created. "
                                                   f"Default is {DEFAULT_NODES_DIR}")

    # Edges file path
    output_files_group.add_argument("-e", "--edges-path", dest="edges_path", action="store", default=DEFAULT_EDGES_DIR,
                                    type=str, help=f"path where the edges file is created. "
                                                   f"Default is {DEFAULT_EDGES_DIR}")

    # Full network file path
    output_files_group.add_argument("-o", "--output-network", dest="network_path", action="store",
                                    default=DEFAULT_NET_DIR, type=str,
                                    help=f"path where the network file is created. Default is {DEFAULT_NET_DIR}")

    # SUMO config file path
    output_files_group.add_argument("-s", "--sumo-config-path", dest="sumo_config_path", action='store',
                                    default=DEFAULT_CONFIG_DIR, type=str, help=f"path where SUMO configuration file is "
                                                                               f"created. Default is "
                                                                               f"{DEFAULT_CONFIG_DIR}")

    # Network Generator
    network_generator_group = arg_parser.add_argument_group("Network generator",
                                                            description="Parameters related to the network generation")
    network_generator_group.add_argument("-r", "--rows", dest="rows", action="store", default=MIN_ROWS,
                                         type=check_dimension, help=f"define the number of rows of the network. "
                                                                    f"Default is {MIN_ROWS}")
    network_generator_group.add_argument("-c", "--cols", dest="cols", action="store", default=MIN_COLS,
                                         type=check_dimension, help=f"define the number of cols of the network. "
                                                                    f"Default is {MIN_COLS}")
    network_generator_group.add_argument("-l", "--lanes", dest="lanes", action="store", default=MIN_LANES,
                                         type=check_greater_zero,
                                         help=f"define the number of lanes per edge. Must be greater than 0. "
                                              f"Default is {MIN_LANES}")
    network_generator_group.add_argument("--distance", dest="distance", action="store", default=DISTANCE,
                                         type=check_greater_zero,
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

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == '__main__':
    # Retrieve execution options (parameters)
    exec_options = get_options()

    print(f"Executing network grid generator with parameters: {vars(exec_options)}")

    # Generate the network file -> Added 2 to the network columns
    generate_network_file(rows=exec_options.rows + 2, cols=exec_options.cols + 2, lanes=exec_options.lanes,
                          distance=exec_options.distance, junction=exec_options.junction,
                          tl_type=exec_options.tl_type, tl_layout=exec_options.tl_layout,
                          nodes_path=exec_options.nodes_path, edges_path=exec_options.edges_path,
                          network_path=exec_options.network_path)

    # Generate the SUMO config file
    generate_sumo_config_file(sumo_config_path=exec_options.sumo_config_path, network_path=exec_options.network_path)
