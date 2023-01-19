import argparse
import os
import sys

import t_predictor.static.constants as cnt
from t_predictor.generators.time_pattern_generator import TimePatternGenerator


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
    arg_parser = argparse.ArgumentParser(description='Script for generating the traffic time pattern based on a working'
                                                     ' calendar.')

    # Input working calendar
    arg_parser.add_argument("-i", "--input-calendar", dest="input_calendar", action='store',
                            help="input working calendar file", required=True)

    # Output traffic time pattern file
    arg_parser.add_argument("-o", "--output-file", dest="output_file", type=str, action="store",
                               default=cnt.DEFAULT_OUTPUT_FILE,
                               help=f"output traffic time pattern file. Default to {cnt.DEFAULT_OUTPUT_FILE}")

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":

    # Import required libraries
    import_required_libs()

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Create the time pattern generator
    time_pattern_generator = TimePatternGenerator(input_file=exec_options.input_calendar)

    # Parse calendar to be valid
    time_pattern_generator.parse_calendar()

    # Get random pattern calendar
    pattern_calendar = time_pattern_generator.get_random_pattern_calendar()

    # Store all the pattern calendar
    pattern_calendar.to_csv(exec_options.output_file, index=False)
