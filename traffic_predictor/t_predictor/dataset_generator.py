import argparse
import os
import sys

import t_predictor.static.constants as cnt
from sumolib import checkBinary
from t_predictor.generators.dataset_generator_time_pattern import TimePatternGenerator
from t_predictor.generators.dataset_generator_traffic_light import TrafficLightTypeGenerator
from t_predictor.static.argparse_types import check_file, check_greater_zero
from t_predictor.visualization.console_visualizer import ConsoleVisualizer


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
    Get options from the execution command

    :return: Arguments options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Script for generating the traffic dataset based on a calendar or '
                                                     'different traffic light types.')

    # Dataset generation group
    dataset_group = arg_parser.add_argument_group("Dataset generator",
                                                  description="Parameters related to the dataset generation")
    dataset_group.add_argument("--nogui", action="store_true", type=bool,
                               default=cnt.DEFAULT_GUI_FLAG, help="run the commandline version of sumo. Default to "
                                                                  f"{cnt.DEFAULT_GUI_FLAG}")
    dataset_group.add_argument("-c", "--config", dest="config", action='store', type=check_file,
                               default=cnt.DEFAULT_CONFIG_FILE,
                               help=f"sumo configuration file location. Default to {cnt.DEFAULT_CONFIG_FILE}")
    dataset_group.add_argument("-n", "--num-sim", dest="num_sim", type=check_greater_zero, action="store",
                               help=f"number of simulations. Default to {cnt.DEFAULT_NUMBER_OF_SIMULATIONS}",
                               default=cnt.DEFAULT_NUMBER_OF_SIMULATIONS)
    dataset_group.add_argument("-t", "--time-pattern", dest="time_pattern", type=check_file, action="store",
                               help="time pattern input file")
    dataset_group.add_argument("-o", "--output-file", dest="output_file", type=check_file, action="store",
                               default=cnt.DEFAULT_OUTPUT_FILE,
                               help=f"output file. Default to {cnt.DEFAULT_OUTPUT_FILE}")

    # Visualization group
    visualization_group = arg_parser.add_argument_group("Visualization tools",
                                                        description="Parameters related to the visualization tools")
    visualization_group.add_argument("--cli-visualize", dest="cli_visualize", action="store_true", type=bool,
                                     default=cnt.DEFAULT_CLI_VISUALIZE_FLAG,
                                     help=f"visualize option by command line. Default to "
                                          f"{cnt.DEFAULT_CLI_VISUALIZE_FLAG}")

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":

    # Import required libraries
    import_required_libs()

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Visualize tool
    if exec_options.cli_visualize:
        console_visualizer = ConsoleVisualizer()
        console_visualizer.execute()

    else:  # Dataset generation tool

        if exec_options.num_sim and exec_options.time_pattern:
            print("Error, the simulation number and the time pattern cannot be used together")
            exit()

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

        # Initialize TraCI sim to None in order to fill later on
        traci_sim = None

        if exec_options.num_sim != 0:
            # Create the TraCI Traffic Light Type simulator
            traci_sim = TrafficLightTypeGenerator(sumo_conf=sim_args, num_sim=exec_options.num_sim)

        elif exec_options.time_pattern != '':
            # Create the TraCI Time Pattern simulator
            traci_sim = TimePatternGenerator(sumo_conf=sim_args, time_pattern_file=exec_options.time_pattern)
        else:
            print('Error in the arguments')
            exit(-1)

        # Perform simulations
        traci_sim.simulate()

        # Store the dataset into the output file
        traci_sim.store_all_data(exec_options.output_file)
