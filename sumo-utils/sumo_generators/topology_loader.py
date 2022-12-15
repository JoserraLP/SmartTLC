import os

import traci
from sumolib import checkBinary
import platform

import xml.etree.cElementTree as ET

from xml.dom import minidom

import pandas as pd

from sumo_generators.generators.detectors_generator import DetectorsGenerator
from sumo_generators.network.models import TrafficLight
from sumo_generators.network.net_topology import NetworkTopology
from sumo_generators.static.argparse_types import *
from sumo_generators.static.constants import *


def get_options():
    """
    Get options from the execution command

    :return: Arguments options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Script that loads a road network topology into a database')

    arg_parser.add_argument("--nogui", action="store_true",
                            default=False, help="run the commandline version of sumo")

    arg_parser.add_argument("-c", "--config", dest="config_file", action='store', default=DEFAULT_CONFIG_FILE,
                            type=check_file, help=f"sumo configuration file location. Default is "
                                                  f"{DEFAULT_CONFIG_FILE}")

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

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


def merge_junctions_df(nodes_df: pd.DataFrame, osm_df: pd.DataFrame):
    """
    Merge junctions dataframes

    :param nodes_df: nodes cartesian dataframe
    :type nodes_df: Pandas DataFrame
    :param osm_df: nodes cartesian dataframe
    :type osm_df: Pandas DataFrame
    :return: dataframe merged
    :rtype: Pandas DataFrame
    """
    # Left as the nod.csv has all the junctions and the osm_df has extra information
    df = nodes_df.merge(osm_df, on=['node_id'], how='left')
    # Remove junctions duplicated
    df = df.drop_duplicates(subset='node_id')
    df = df[['node_id', 'node_x', 'node_y', 'node_lat', 'node_lon', 'node_type']]
    return df


def generate_detectors(net_topology: NetworkTopology, detector_file: str) -> None:
    """
    Generate detectors on database and store them into an output file

    :param net_topology: network topology database
    :type net_topology: NetworkTopology
    :param detector_file: e1 detector file
    :type detector_file: str
    :return: None
    """
    # Create detector generator instance
    detector_generator = DetectorsGenerator()

    # Retrieve all the traffic lights
    traffic_lights = TrafficLight.nodes.all()

    # Create list with all detectors
    all_detectors = []

    # Iterate over all traffic lights
    for traffic_light in traffic_lights:
        # Retrieve ingoing roads
        _, ingoing_roads = net_topology.get_tl_roads(traffic_light.name)

        # Iterate over all roads
        for road in ingoing_roads:
            # Get lane length
            road_length = road.distance
            # Get valid pos as sometimes the road can be shorter than the distance specified
            pos = str(road_length - 0.01) if DEFAULT_DETECTOR_POS > road_length else str(DEFAULT_DETECTOR_POS)
            # Created with default values
            detector = {'id': 'e1detector_' + road.name, 'lane': road.name, 'pos': pos,
                        'freq': str(DEFAULT_DETECTOR_FREQ),
                        'file': 'NUL'}
            # Append detector to list
            all_detectors.append(detector)
            # Create the database detector and its relation
            net_topology.create_detector_node_relation(detector)

    # Add all the detectors
    detector_generator.add_detectors(all_detectors)

    # Store the detectors into the generator
    detector_generator.store_detectors()

    # Write into the file
    detector_generator.write_output_file(detector_file)


def process_topology_files(config_file: str) -> None:
    """
    Process from XML to CSV topology files

    :param config_file: SUMO configuration file
    :type config_file: str
    :return: None
    """

    # Get SUMO tools directory
    sumo_xml2csv_tool_dir = '$SUMO_HOME/tools/xml/xml2csv.py' if platform.system() == 'Linux' \
        else '\"%SUMO_HOME%/tools/xml/xml2csv.py\"'
    # Retrieve topology dir
    base_dir, config_file_name = '/'.join(config_file.split('/')[:-1]) + '/', config_file.split('/')[-1]

    # Get topology file
    topology_file = 'topology.net.xml' if 'osm' not in config_file_name else 'osm.net.xml'

    # Execute the netconvert command to guess traffic lights if retrieved from 'osm'
    if 'osm' in config_file_name:
        # Guess TL
        os.system(f"netconvert --osm {base_dir}osm_bbox.osm.xml -o {base_dir}osm.net.xml --geometry.remove "
                  f"--ramps.guess --junctions.join --tls.guess-signals --tls.discard-simple ")

        # Remove pedestrian areas. Execute afterwards as some TL are guessed based on pedestrian lanes
        os.system(f"netconvert -s {base_dir}osm.net.xml -o {base_dir}osm.net.xml --remove-edges.by-vclass pedestrian")

    # Generate the topology edges on plain text
    os.system(f"netconvert -s {base_dir}{topology_file} --plain-output-prefix {base_dir}plain")
    # Generate the edges CSV
    os.system(f"python {sumo_xml2csv_tool_dir} {base_dir}plain.edg.xml")
    # Generate the junctions CSV
    os.system(f"python {sumo_xml2csv_tool_dir} {base_dir}plain.nod.xml")
    # Generate the OSM junctions CSV
    if os.path.exists(f"{base_dir}osm_bbox.osm.xml"):
        os.system(f"python {sumo_xml2csv_tool_dir} {base_dir}osm_bbox.osm.xml")


def update_config_file(config_file: str) -> None:
    """
    Update the SUMO configuration file and store the new detector file

    :param config_file: SUMO configuration file
    :type config_file: str
    :return: None
    """
    # Load config file
    tree = ET.parse(config_file)
    # Get root item
    root = tree.getroot()
    # Find input tag
    input_tag = root.find('input')
    # Check if additional-files tag is defined previously
    additional_files = input_tag.find('additional-files')

    # Check if the tag exists and has items
    if additional_files is not None and additional_files.items():
        # Check if it is stored previously
        if DEFAULT_DETECTOR_FILE not in additional_files.get('value'):
            # Append new value
            additional_files.set('value', additional_files.get('value') + ',' + DEFAULT_DETECTOR_FILE)
    else:
        # Add additional-files tag to input tag
        addition_files = ET.SubElement(input_tag, 'additional-files')
        # Set value to file
        addition_files.set('value', DEFAULT_DETECTOR_FILE)

    # Write output file
    tree.write(config_file)


def load_topology(config_file: str, database_params: dict):
    """
    Load topology into database

    :param config_file: SUMO configuration file
    :type config_file: str
    :param database_params: database connections params
    :type database_params: dict
    """
    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    traci.start([sumoBinary, "-c", exec_options.config_file])

    # Create network topology database connector
    net_topology = NetworkTopology(ip_address=database_params['ip_address'],
                                   user=database_params['user'],
                                   password=database_params['password'],
                                   traci=traci)

    # Clear the database of pre-existent data
    net_topology.clear_database()

    # Get base topology dir
    directory = '/'.join(config_file.split('/')[:-1]) + '/'

    # Get Edges dataframe
    edges_df = pd.read_csv(directory + 'plain.edg.csv', delimiter=';')
    # Get only valid values (remove NaN) and drop duplicates
    edges_df = edges_df[edges_df['edge_id'].notna()].drop_duplicates(subset='edge_id')

    # Get junctions dataframe -> Cartesian info
    junctions_df = pd.read_csv(directory + 'plain.nod.csv', delimiter=';').drop(index=0)

    # Get junctions dataframe if available -> Geographical info
    if os.path.isfile(directory + 'osm_bbox.osm.csv'):
        # Used on_bad_lines to 'skip' as the parser sometimes generates additional ';'
        junctions_osm_df = pd.read_csv(directory + 'osm_bbox.osm.csv', delimiter=';', on_bad_lines='skip',
                                       dtype={'node_id': str})
        # Get only valid values (remove NaN)
        junctions_osm_df = junctions_osm_df[junctions_osm_df['node_id'].notna()]

        # Merge both items
        junctions_df = merge_junctions_df(junctions_df, junctions_osm_df)

    # Get only valid values (remove NaN)
    junctions_df = junctions_df[junctions_df['node_id'].notna()]

    # Load topology data
    net_topology.load_data(edges_df, junctions_df)

    # Create detector file path based on config file
    detector_file = '/'.join(config_file.split('/')[:-1]) + '/' + DEFAULT_DETECTOR_FILE

    # Generate detectors
    generate_detectors(net_topology=net_topology, detector_file=detector_file)

    # Update the sumocfg file with the detectors
    update_config_file(config_file=config_file)

    # Close database network connection
    net_topology.close()

    # Close TraCI connection
    traci.close()


if __name__ == '__main__':
    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Process the topology files
    process_topology_files(config_file=exec_options.config_file)

    # Create dict with topology database params
    topology_database_params = {'ip_address': exec_options.topology_db_ip,
                                'user': exec_options.topology_db_user,
                                'password': exec_options.topology_db_password}

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if exec_options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # Load topology
    load_topology(config_file=exec_options.config_file, database_params=topology_database_params)
