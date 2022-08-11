import argparse
import random

from sumo_generators.generators.flows_generator import FlowsGenerator
from sumo_generators.generators.sumo_config_generator import SumoConfigGenerator
from sumo_generators.static.constants import FLOWS_VALUES
from t_predictor.generators.time_pattern_generator import TimePatternGenerator
from t_predictor.generators.tl_program_generator import TrafficLightProgramGenerator
from t_predictor.static.constants import DEFAULT_GENERATED_CALENDAR_FILE


def get_options():
    """
    Get options from the execution command

    :return: Arguments options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Script for generating traffic lights, SUMO configuration file, '
                                                     'vehicle flows and calendar.')

    # TL program file
    arg_parser.add_argument("-t", "--tl-program-file", dest="tl_program_file", action='store',
                            help="sumo traffic lights programs file location")

    # SUMO configuration file
    arg_parser.add_argument("-s", "--sumo-config-file", dest="sumo_config_file", action='store',
                            help="sumo configuration file location")

    # Flows configuration file
    arg_parser.add_argument("-f", "--flows-config-file", dest="flows_config_file", action='store',
                            help="flow configuration file")

    # Calendar dataset generation
    arg_parser.add_argument("-c", "--calendar", dest="calendar_file", action='store',
                            help="calendar file")

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":
    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Generate TL program file
    if exec_options.tl_program_file:
        # Define the generator
        tl_generator = TrafficLightProgramGenerator()

        # Create the static phases
        static_phases = [{"duration": "30", "state": "GGGGrrrrGGGGrrrr"},
                         {"duration": "5", "state": "yyGGrrrryyGGrrrr"},
                         {"duration": "5", "state": "rrGGrrrrrrGGrrrr"}, {"duration": "5", "state": "rryyrrrrrryyrrrr"},
                         {"duration": "30", "state": "rrrrGGGGrrrrGGGG"},
                         {"duration": "5", "state": "rrrryyGGrrrryyGG"},
                         {"duration": "5", "state": "rrrrrrGGrrrrrrGG"}, {"duration": "5", "state": "rrrrrryyrrrrrryy"}]

        tl_generator.add_static_program(static_phases)

        # Create the actuated phases
        actuated_phases = [{"duration": "30", "minDur": "20", "maxDur": "40", "state": "GGGGrrrrGGGGrrrr"},
                           {"duration": "5", "minDur": "5", "maxDur": "5", "state": "yyGGrrrryyGGrrrr"},
                           {"duration": "5", "minDur": "5", "maxDur": "5", "state": "rrGGrrrrrrGGrrrr"},
                           {"duration": "5", "minDur": "5", "maxDur": "5", "state": "rryyrrrrrryyrrrr"},
                           {"duration": "30", "minDur": "20", "maxDur": "40", "state": "rrrrGGGGrrrrGGGG"},
                           {"duration": "5", "minDur": "5", "maxDur": "5", "state": "rrrryyGGrrrryyGG"},
                           {"duration": "5", "minDur": "5", "maxDur": "5", "state": "rrrrrrGGrrrrrrGG"},
                           {"duration": "5", "minDur": "5", "maxDur": "5", "state": "rrrrrryyrrrrrryy"}]

        tl_generator.add_actuated_program(actuated_phases)

        # Define the actuated time gap parameters
        time_gap_params = [("max-gap", "3.0"), ("detector-gap", "2.0"), ("passing-time", "2.0"), ("vTypes", ""),
                           ("show-detectors", "false"), ("file", "NULL"), ("freq", "300")]
        tl_generator.add_actuated_program(actuated_phases, params_type="time_gap", params=time_gap_params)

        # Define the actuated time loss parameters
        time_loss_params = [("detectorRange", "100"), ("minTimeLoss", "2"), ("show-detectors", "false"),
                            ("file", "NULL"),
                            ("freq", "300")]
        tl_generator.add_actuated_program(actuated_phases, params_type="time_loss", params=time_loss_params)

        # Save the programs into an output file
        tl_generator.write_output_file(exec_options.tl_program_file)

    # Generate SUMO config file
    if exec_options.sumo_config_file:
        # Define the generator
        sumo_config_generator = SumoConfigGenerator()

        # Define the input files
        input_files = {
            'net-file': '../topology/topology.net.xml',
            'route-files': '../flows/flows.rou.xml',
            'gui-settings-file': '../topology/topology.view.xml',
            'additional-files': "../topology/topology.tll.xml,../topology/topology.det.xml"
        }

        # Set input configuration files
        sumo_config_generator.set_input_files(input_files)

        # Define simulation begin time
        sumo_config_generator.set_begin_time(0)

        # Define the report policy
        policy = {'verbose': 'true', 'no-step-log': 'true'}

        # Set report policy
        sumo_config_generator.set_report_policy(policy)

        # Save the programs into an output file
        sumo_config_generator.write_output_file(exec_options.sumo_config_file)

    # Generate flows file
    if exec_options.flows_config_file:
        # Define the generator
        flows_generator = FlowsGenerator()

        # There are 4 possible begins and 3 possible ends for each one

        # Only retrieve the high values. This is a basic example
        vehs_per_hour = FLOWS_VALUES['high']['vehsPerHour']
        vehs_range = FLOWS_VALUES['high']['vehs_range']

        # Define the flows
        flows = [
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 'n1i', 'to': 'e1o'},
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 'n1i', 'to': 's1o'},
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 'n1i', 'to': 'w1o'},
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 'e1i', 'to': 's1o'},
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 'e1i', 'to': 'w1o'},
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 'e1i', 'to': 'n1o'},
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 's1i', 'to': 'w1o'},
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 's1i', 'to': 'n1o'},
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 's1i', 'to': 'e1o'},
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 'w1i', 'to': 'n1o'},
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 'w1i', 'to': 'e1o'},
            {'begin': 0, 'end': 500,
             'vehsPerHour': random.randint(vehs_per_hour - vehs_range, vehs_per_hour + vehs_range),
             'from': 'w1i', 'to': 's1o'}
        ]

        flows_generator.add_flows(flows)

        # Save the programs into an output file
        flows_generator.write_output_file(exec_options.flows_config_file)

    # Generate the time pattern csv from the calendar
    if exec_options.calendar_file:
        # Create the time pattern generator
        time_pattern_generator = TimePatternGenerator(input_file=exec_options.calendar_file)

        # Get random pattern calendar
        random_pattern_calendar = time_pattern_generator.get_random_pattern_calendar()

        # Store all the year
        random_pattern_calendar.to_csv(DEFAULT_GENERATED_CALENDAR_FILE, index=False)
