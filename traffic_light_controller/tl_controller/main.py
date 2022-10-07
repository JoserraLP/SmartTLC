import argparse
import os
import sys

import tl_controller.static.constants as cnt
from sumolib import checkBinary
from tl_controller.providers.traci_sim import TraCISimulator
from tl_controller.static.argparse_types import check_file, check_valid_format, check_valid_predictor_value


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

    arg_parser.add_argument("--nogui", action="store_true",
                            default=cnt.DEFAULT_GUI_FLAG, help="run the commandline version of sumo")
    arg_parser.add_argument("--local", dest="local", action="store_true", default=False,
                            help="run the component locally. It will not connect to middleware.")
    arg_parser.add_argument("-c", "--config", dest="config_file", action='store', default=cnt.DEFAULT_CONFIG_FILE,
                            type=check_file, help=f"sumo configuration file location. Default is "
                                                  f"{cnt.DEFAULT_CONFIG_FILE}")
    arg_parser.add_argument("-t", "--time-pattern", dest="time_pattern", metavar='FILE', action="store",
                            help="time pattern input file. Do not use it with the dates parameter.")
    arg_parser.add_argument("-d", "--dates", dest="dates", action="store", type=check_valid_format,
                            help="calendar dates from start to end to simulate. Format is dd/mm/yyyy-dd/mm/yyyy.")
    arg_parser.add_argument("--turn-pattern", dest="turn_pattern", action="store", type=check_file,
                            help="turn pattern input file.")
    arg_parser.add_argument("-s", "--save-vehicles", action="store", dest="save_vehicles_dir", type=str,
                            help="directory where the vehicles routes will be saved. Cannot be used with the "
                                 "--load-vehicles option.")
    arg_parser.add_argument("-l", "--load-vehicles", action="store", default=False, dest="load_vehicles_dir",
                            type=check_file,
                            help="directory from where the vehicles routes will be load. Cannot be used with the "
                                 "--save-vehicles option. Default to False.")
    arg_parser.add_argument("--traffic-analyzer", action="store", dest="traffic_analyzer", type=str,
                            help="enable traffic analyzer on traffic lights. Can be 'all' or the names of the "
                                 "traffic lights split by ','.")
    arg_parser.add_argument("--turn-predictor", action="store", dest="turn_predictor", type=str,
                            help="enable turn predictor on traffic lights. Can be 'all' or the names of the "
                                 "traffic lights split by ','.")
    arg_parser.add_argument("--traffic-predictor", action="store", dest="traffic_predictor", type=str,
                            help="enable traffic predictor on traffic lights. Can be 'all' or the names of the "
                                 "traffic lights split by ','.")
    arg_parser.add_argument("--traffic-predictor-type", action="store", dest="traffic_predictor_type",
                            type=check_valid_predictor_value, default="date",
                            help="select the traffic predictor type. Possible values are 'date' and 'context'. "
                                 "Default to 'date'.")

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":

    # Import required libraries
    import_required_libs()

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Check invalid arguments
    if exec_options.save_vehicles_dir and exec_options.load_vehicles_dir:
        print("Please, use the correct arguments")
        exit(-1)

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
                                   turn_pattern_file=exec_options.turn_pattern, local=exec_options.local)
    elif exec_options.dates:
        traci_sim = TraCISimulator(sumo_conf=sim_args, dates=exec_options.dates,
                                   turn_pattern_file=exec_options.turn_pattern, local=exec_options.local)

    # Get simulation params
    simulation_params = traci_sim.retrieve_simulation_params(load_vehicles_dir=exec_options.load_vehicles_dir,
                                                             save_vehicles_dir=exec_options.save_vehicles_dir)

    # Initialize the simulation topology
    traci_sim.initialize_simulation_topology(traffic_analyzer=exec_options.traffic_analyzer,
                                             turn_predictor=exec_options.turn_predictor,
                                             traffic_predictor=exec_options.traffic_predictor,
                                             traffic_predictor_type=exec_options.traffic_predictor_type,
                                             simulation_params=simulation_params)

    # Start the simulation process
    traci_sim.simulate(load_vehicles_dir=exec_options.load_vehicles_dir)
