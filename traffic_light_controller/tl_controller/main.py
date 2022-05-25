import optparse
import os
import sys

import tl_controller.static.constants as cnt
from sumolib import checkBinary
from tl_controller.providers.traci_sim import TraCISimulator, DEFAULT_TURN_PATTERN_FILE


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
    simulation_group.add_option("-t", "--time-pattern", dest="time_pattern", metavar='FILE', action="store",
                                help="time pattern input file. Do not use it with the dates parameter.")
    simulation_group.add_option("-d", "--dates", dest="dates", action="store",
                                help="calendar dates from start to end to simulate. Format is dd/mm/yyyy-dd/mm/yyyy."
                                     "")
    simulation_group.add_option("--turn-pattern", dest="turn_pattern", metavar='FILE', action="store",
                                help="turn pattern input file.")
    simulation_group.add_option("-s", "--save-vehicles", action="store", dest="save_vehicles_dir",
                                help="directory where the vehicles info will be saved. Cannot be used with the "
                                     "--load-vehicles option.")
    simulation_group.add_option("-l", "--load-vehicles", action="store", dest="load_vehicles_dir",
                                help="directory from where the vehicles info will be load. Cannot be used with the "
                                     "--save-vehicles option.")

    optParser.add_option_group(simulation_group)

    options, args = optParser.parse_args()
    return options


if __name__ == "__main__":

    # Wait 120 seconds until the other components are deployed
    # time.sleep(120)

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

    # Initialize to None
    traci_sim = None

    # Create the TraCI Traffic simulator based on time pattern or dates
    if exec_options.time_pattern:
        traci_sim = TraCISimulator(sumo_conf=sim_args, time_pattern_file=exec_options.time_pattern,
                                   turn_pattern_file=exec_options.turn_pattern)
    elif exec_options.dates:
        traci_sim = TraCISimulator(sumo_conf=sim_args, dates=exec_options.dates,
                                   turn_pattern_file=exec_options.turn_pattern)

    # Start the simulation process
    traci_sim.simulate(load_vehicles_dir=exec_options.load_vehicles_dir,
                       save_vehicles_dir=exec_options.save_vehicles_dir)
