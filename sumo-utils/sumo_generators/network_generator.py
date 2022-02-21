import subprocess

from sumo_generators.network.net_generator import NetGenerator
from sumo_generators.static.argparse_types import *
from sumo_generators.static.constants import *


def generate_network_file(rows: int = MIN_ROWS, cols: int = MIN_COLS, lanes: int = MIN_LANES, distance: int = DISTANCE,
                          junction: str = JUNCTION_TYPE, tl_type: str = TL_TYPE, tl_layout: str = TL_LAYOUT,
                          nodes_path: str = DEFAULT_NODES_DIR, edges_path: str = DEFAULT_EDGES_DIR,
                          network_path: str = DEFAULT_NET_DIR):
    """
    Creates the network generator and generates the output network file

    :param rows: number of rows of the matrix
    :type rows: int
    :param cols: number of cols of the matrix
    :type rows: int
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

    # Define the arguments options
    arg_parser.add_argument("-r", "--rows", dest="rows", action="store", type=check_dimension,
                            help=f"define the number of rows of the network. Must be greater than 2. Default is "
                                 f"{MIN_ROWS}", default=MIN_ROWS)
    arg_parser.add_argument("-c", "--cols", dest="cols", action="store", type=check_dimension,
                            help=f"define the number of cols of the network. Must be greater than 2. Default is "
                                 f"{MIN_COLS}", default=MIN_COLS)
    arg_parser.add_argument("-l", "--lanes", dest="lanes", action="store", type=int,
                            help=f"define the number of lanes per edge. Must be greater than 0. Default is {MIN_LANES}",
                            default=MIN_LANES)
    arg_parser.add_argument("-d", "--distance", dest="distance", action="store", type=float,
                            help=f"define the distance between the nodes. Must be greater than 0. Default is {DISTANCE}"
                            , default=DISTANCE)
    arg_parser.add_argument("-j", "--junction", dest="junction", action="store", type=check_valid_junction_type,
                            help="define the junction type on central nodes. Possible types are: priority, "
                                 "traffic_light, right_before_left, priority_stop, allway_stop, "
                                 f"traffic_light_right_on_red. Default is {JUNCTION_TYPE}.", default=JUNCTION_TYPE)
    arg_parser.add_argument("--tl-type", dest="tl_type", action="store", type=check_valid_tl_type,
                            help="define the tl type, only if the 'junction' value is 'traffic_light'. "
                                 f"Possible types are: static, actuated, delay_based. Default is {TL_TYPE}.",
                            default=TL_TYPE)
    arg_parser.add_argument("--tl-layout", dest="tl_layout", action="store", type=check_valid_tl_layout,
                            help="define the tl layout, only if the 'junction' value is 'traffic_light'. "
                                 f"Possible types are: opposites, incoming, alternateOneWay. Default is {TL_LAYOUT}.",
                            default=TL_LAYOUT)
    arg_parser.add_argument("-n", "--nodes", dest="nodes_path", action="store", default=DEFAULT_NODES_DIR, type=str,
                            help="define the path where the nodes file is created")
    arg_parser.add_argument("-e", "--edges", dest="edges_path", action="store", default=DEFAULT_EDGES_DIR, type=str,
                            help="define the path where the edges file is created")
    arg_parser.add_argument("-o", "--output-network", dest="net_path", action="store", default=DEFAULT_NET_DIR,
                            type=str, help="define the path where the network file is created")

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
                          network_path=exec_options.net_path)
