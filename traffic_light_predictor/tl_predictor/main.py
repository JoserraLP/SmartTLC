import optparse
import os
import sys

from sumolib import checkBinary

from tl_predictor.providers.traci_time_pattern_sim import TimePatternSimulator
from tl_predictor.providers.traci_traffic_light_sim import TrafficTypeSimulator
from tl_predictor.visualization.console_visualizer import ConsoleVisualizer
import tl_predictor.static.constants as cnt


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
    Define options for the executable script.

    :return: options
    :rtype: object
    """
    optParser = optparse.OptionParser()

    # Dataset generation group
    dataset_group = optparse.OptionGroup(optParser, "Dataset Generation Options", "Generation tools")
    dataset_group.add_option("--nogui", action="store_true",
                             default=cnt.DEFAULT_GUI_FLAG, help="run the commandline version of sumo")
    dataset_group.add_option("-c", "--config", dest="config", action='store',
                             metavar="FILE", help="sumo configuration file location")
    dataset_group.add_option("-n", "--num-sim", dest="num_sim", type='int', action="store",
                             help="number of simulations", default=cnt.DEFAULT_NUMBER_OF_SIMULATIONS)
    dataset_group.add_option("-t", "--time-pattern", dest="time_pattern", metavar='FILE', action="store",
                             help="time pattern input file")
    dataset_group.add_option("-o", "--output-file", dest="output_file", metavar='FILE', action="store",
                             help="output file")
    optParser.add_option_group(dataset_group)

    # Visualization group
    visualization_group = optparse.OptionGroup(optParser, "Visualization Options", "Visualization tools")
    visualization_group.add_option("--cli-visualize", dest="cli_visualize", action="store_true",
                                   default=cnt.DEFAULT_CLI_VISUALIZE_FLAG, help="visualize option by command line")
    optParser.add_option_group(visualization_group)

    options, args = optParser.parse_args()
    return options


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

        # Retrieve configuration file by parameters or by default
        if exec_options.config:
            config_file = exec_options.config
        else:
            config_file = cnt.DEFAULT_CONFIG_FILE

        # Define the output file by parameters or by default
        if exec_options.output_file:
            output_file = exec_options.output_file
        else:
            output_file = cnt.DEFAULT_OUTPUT_FILE

        # Create a dict with the simulation arguments
        sim_args = {
            'config_file': config_file,
            'sumo_binary': sumo_binary
        }

        # Initialize TraCI sim to None in order to fill later on
        traci_sim = None

        if exec_options.num_sim != 0:
            # Create the TraCI Traffic Type simulator
            traci_sim = TrafficTypeSimulator(sumo_conf=sim_args, num_sim=exec_options.num_sim)

        elif exec_options.time_pattern != '':
            # Create the TraCI Time Pattern simulator
            traci_sim = TimePatternSimulator(sumo_conf=sim_args, time_pattern_file=exec_options.time_pattern)
        else:
            print('Error in the arguments')
            exit(-1)

        # Perform simulations
        traci_sim.simulate()

        # Store the dataset into the output file
        traci_sim.store_all_data(output_file)
