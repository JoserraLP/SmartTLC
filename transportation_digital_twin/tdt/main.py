import argparse
import os
import sys

import tdt.static.constants as cnt
from sumolib import checkBinary

from sumo_generators.static.constants import MQTT_URL, MQTT_PORT, DB_USER, DB_PASSWORD, DB_IP_ADDRESS, \
    DEFAULT_TEMPORAL_WINDOW
from tdt.providers.traci_sim import TraCISimulator
from tdt.static.argparse_types import check_file, check_valid_format


def import_required_libs():
    """
    Import required libraries from SUMO because we need to import python modules from the $SUMO_HOME/tools directory.

    :return: None
    """
    if 'SUMO_HOME' in os.environ:
        # Retrieve the tools and append the into the system
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        # Close script
        sys.exit("please declare environment variable 'SUMO_HOME'")


def get_options():
    """
    Get options for the executable script.

    :return: Arguments options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Script to deploy the TLC component, which is the Transportation'
                                                     'Digital Twin that will simulate the traffic experiment.')

    # Simulation group params
    simulation_group = arg_parser.add_argument_group("Simulation options", description="Parameters related to the "
                                                                                       "simulation")
    simulation_group.add_argument("--nogui", action="store_true",
                                  default=cnt.DEFAULT_GUI_FLAG, help="run the commandline version of sumo")
    simulation_group.add_argument("-c", "--config", dest="config_file", action='store', default=cnt.DEFAULT_CONFIG_FILE,
                                  type=check_file, help=f"sumo configuration file location. Default is "
                                                        f"{cnt.DEFAULT_CONFIG_FILE}")
    simulation_group.add_argument("-t", "--time-pattern", dest="time_pattern", metavar='FILE', action="store",
                                  help="time pattern input file. Do not use it with the dates parameter.")
    simulation_group.add_argument("-d", "--dates", dest="dates", action="store", type=check_valid_format,
                                  help="calendar dates from start to end to simulate. Format is dd/mm/yyyy-dd/mm/yyyy.")
    simulation_group.add_argument("-l", "--load-vehicles", action="store", default=False, dest="load_vehicles_dir",
                                  type=check_file,
                                  help="directory from where the vehicles routes will be load. Default to False.")
    simulation_group.add_argument("--temporal-window", action="store", default=DEFAULT_TEMPORAL_WINDOW,
                                  dest="temporal_window", help="temporal window used to gather contextual information"
                                                               "and adaptation process. It is represented as number of "
                                                               "traffic lights cycles. Default to "
                                                               f"{DEFAULT_TEMPORAL_WINDOW}")

    # Middleware group params
    middleware_group = arg_parser.add_argument_group("Middleware options", description="Parameters related to the "
                                                                                       "middleware connection")
    middleware_group.add_argument("--middleware-host", dest="mqtt_url", action="store", type=str,
                                  help=f"middleware broker host. Default is {MQTT_URL}", default=MQTT_URL)
    middleware_group.add_argument("--middleware-port", dest="mqtt_port", action="store", type=int,
                                  help=f"middleware broker port. Default is {MQTT_PORT}", default=MQTT_PORT)
    middleware_group.add_argument("--local", dest="local", action="store_true", default=False,
                                  help="run the component locally. It will not connect to middleware.")

    # Traffic light additional components
    tl_components_group = arg_parser.add_argument_group("Traffic Light additional component options",
                                                        description="Parameters related to the additional components"
                                                                    " that can be installed on a traffic light"
                                                                    " (Traffic analyzer, traffic predictor and turn"
                                                                    " predictor)")
    tl_components_group.add_argument("--traffic-analyzer", action="store", dest="traffic_analyzer", type=str,
                                     help="enable traffic analyzer on traffic lights. Can be 'all' or the names of the "
                                          "traffic lights split by ','.")
    tl_components_group.add_argument("--turn-predictor", action="store", dest="turn_predictor", type=str,
                                     help="enable turn predictor on traffic lights. Can be 'all' or the names of the "
                                          "traffic lights split by ','.")
    tl_components_group.add_argument("--traffic-predictor", action="store", dest="traffic_predictor", type=str,
                                     help="enable traffic predictor on traffic lights. Can be 'all' or the names of "
                                          "the traffic lights split by ','.")

    # Network topology database params
    network_topology_group = arg_parser.add_argument_group("Network topology database options",
                                                           description="Parameters related to the network topology "
                                                                       "database connection")
    network_topology_group.add_argument("--topology-db-ip", action="store", dest="topology_db_ip",
                                        type=str, default=DB_IP_ADDRESS,
                                        help=f"topology database ip address with port. Default to {DB_IP_ADDRESS}")
    network_topology_group.add_argument("--topology-db-user", action="store", dest="topology_db_user",
                                        type=str, default=DB_USER, help=f"topology database user. Default to {DB_USER}")
    network_topology_group.add_argument("--topology-db-password", action="store", dest="topology_db_password",
                                        type=str, default=DB_PASSWORD,
                                        help=f"topology database user password. Default to {DB_PASSWORD}")

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":

    # Import required libraries
    import_required_libs()

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if exec_options.nogui:
        sumo_binary = checkBinary('sumo')
    else:
        sumo_binary = checkBinary('sumo-gui')

    # Create a dict with the simulation arguments
    sim_args = {
        'config_file': exec_options.config_file,
        'sumo_binary': sumo_binary
    }

    # Initialize to None
    traci_sim = None

    # Create the TraCI Traffic simulator based on time pattern or dates
    if exec_options.time_pattern:
        traci_sim = TraCISimulator(sumo_conf=sim_args, time_pattern_file=exec_options.time_pattern,
                                   local=exec_options.local, mqtt_url=exec_options.mqtt_url,
                                   mqtt_port=exec_options.mqtt_port)
    elif exec_options.dates:
        traci_sim = TraCISimulator(sumo_conf=sim_args, dates=exec_options.dates, local=exec_options.local,
                                   mqtt_url=exec_options.mqtt_url, mqtt_port=exec_options.mqtt_port)

    # Get simulation params
    simulation_params = traci_sim.retrieve_simulation_params(load_vehicles_dir=exec_options.load_vehicles_dir)

    # Create dict with topology database params
    topology_database_params = {'ip_address': exec_options.topology_db_ip,
                                'user': exec_options.topology_db_user,
                                'password': exec_options.topology_db_password}

    # Initialize the simulation topology
    traci_sim.initialize_simulation_topology(traffic_analyzer=exec_options.traffic_analyzer,
                                             turn_predictor=exec_options.turn_predictor,
                                             traffic_predictor=exec_options.traffic_predictor,
                                             simulation_params=simulation_params,
                                             topology_database_params=topology_database_params)

    # Start the simulation process
    traci_sim.simulate()
