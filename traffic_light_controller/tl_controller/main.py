import optparse
import os
import sys

import tl_controller.static.constants as cnt
from sumolib import checkBinary
from tl_controller.providers.traci_sim import TraCISimulator


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
    simulation_group = optparse.OptionGroup(optParser, "Simulation Options", "Simulation tools")
    simulation_group.add_option("--nogui", action="store_true",
                                default=cnt.DEFAULT_GUI_FLAG, help="run the commandline version of sumo")
    simulation_group.add_option("-c", "--config", dest="config", action='store',
                                metavar="FILE", help="sumo configuration file location")
    simulation_group.add_option("-a", "--analyzer", dest="analyzer", action="store_true",
                                default=False, help="enable analyzer on the simulation.")
    simulation_group.add_option("-t", "--time-pattern", dest="time_pattern", metavar='FILE', action="store",
                                help="time pattern input file")
    optParser.add_option_group(simulation_group)

    options, args = optParser.parse_args()
    return options


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

    # Retrieve configuration file by parameters or by default
    if exec_options.config:
        config_file = exec_options.config
    else:
        config_file = cnt.DEFAULT_CONFIG_FILE

    # Create a dict with the simulation arguments
    sim_args = {
        'config_file': config_file,
        'sumo_binary': sumo_binary
    }

    # Create the TraCI Traffic simulator
    traci_sim = TraCISimulator(sumo_conf=sim_args, time_pattern_file=exec_options.time_pattern,
                               analyzer=exec_options.analyzer)

    traci_sim.simulate()
