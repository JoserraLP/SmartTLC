import xml.etree.ElementTree as ET

from sumo_generators.generators.utils import generate_flow_file
from sumo_generators.network.net_topology import NetworkTopology
from sumo_generators.static.argparse_types import *
from sumo_generators.static.constants import *


def process_turn_definition_file(file_dir: str) -> None:
    """
    Replace on generated file the tag <turns> to <edgeRelations> and remove 100 probability turns

    :param file_dir: turn definition file path
    :type file_dir: str
    :return: None
    """
    # Read file
    tree = ET.parse(file_dir)
    # Get root
    root = tree.getroot()
    # Replace root tag
    root.tag = "edgeRelations"
    # Remove attributes
    root.attrib = {}

    # Iterate over all the intervals
    for interval in root.findall('interval'):
        # Iterate over the edge relations
        for edge_relation in interval.findall('edgeRelation'):
            # Remove those with probability = 100
            if int(edge_relation.attrib['probability']) == 100:
                interval.remove(edge_relation)

    # Write on output file
    tree.write(file_dir)


def get_options():
    """
    Get options from the execution command

    :return: Arguments options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Script that generates turn definitions and traffic trips/flows')

    arg_parser.add_argument("--nogui", action="store_true",
                            default=False, help="run the commandline version of sumo")

    arg_parser.add_argument("-o", "--output-folder", dest="output_folder", action='store', default=DEFAULT_DIR,
                            type=str, help=f"output folder where the related files will be generated. Default is "
                                           f"{DEFAULT_DIR}")

    # Database group
    database_group = arg_parser.add_argument_group("Database parameters",
                                                   description="Parameters related to the database")
    database_group.add_argument("--topology-db-ip", action="store", dest="topology_db_ip",
                                type=str, default=DB_IP_ADDRESS,
                                help=f"topology database ip address with port. Default to {DB_IP_ADDRESS}")
    database_group.add_argument("--topology-db-user", action="store", dest="topology_db_user",
                                type=str, default=DB_USER, help=f"topology database user. Default to {DB_USER}")
    database_group.add_argument("--topology-db-password", action="store", dest="topology_db_password",
                                type=str, default=DB_PASSWORD,
                                help=f"topology database user password. Default to {DB_PASSWORD}")

    # Flows Generator
    flows_generator_group = arg_parser.add_argument_group("Flows generator",
                                                          description="Parameters related to the flows generation")
    flows_generator_group.add_argument("--time-pattern", dest="time_pattern_path", action='store',
                                       type=str, help=f"time pattern to create the flows.")

    flows_generator_group.add_argument("--dates", dest="dates", action="store", type=str,
                                       help="calendar dates from start to end to simulate. Format is "
                                            "dd/mm/yyyy-dd/mm/yyyy.")

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == '__main__':
    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Output folder and files
    output_folder = exec_options.output_folder
    flows_file, connections_file, turn_definitions_file = f"{output_folder}flows.rou.xml",\
                                                          f"{output_folder}plain.con.xml",\
                                                          f"{output_folder}output.turndefs.xml",

    # Create network topology database connection
    net_topology = NetworkTopology(ip_address=exec_options.topology_db_ip, user=exec_options.topology_db_user,
                                   password=exec_options.topology_db_password, traci=None)

    if exec_options.dates:
        # Generate flow file based on date interval
        generate_flow_file(dates=exec_options.dates, flows_path=flows_file, net_topology=net_topology)
    elif exec_options.time_pattern_path:
        # Generate flow file based on time pattern
        generate_flow_file(time_pattern_path=exec_options.time_pattern_path, flows_path=flows_file,
                           net_topology=net_topology)

    # Generate turn definitions
    # Now it is done with default values calculated based on topology
    os.system(f'python "%SUMO_HOME%/tools/turn-defs/generateTurnDefs.py" '
              f'--connections-file {connections_file} '
              f'--turn-definitions-file {turn_definitions_file}')

    # Process invalid data in turn definition file
    process_turn_definition_file(file_dir=turn_definitions_file)

    # Execute jtrrouter to generate the routes files based on flows, turns and net file
    os.system(f'jtrrouter --route-files={flows_file}.flows '
              f'--turn-ratio-files={output_folder}output.turndefs.xml '
              f'--net-file={output_folder}topology.net.xml '
              f'--output-file={flows_file} --accept-all-destinations')
