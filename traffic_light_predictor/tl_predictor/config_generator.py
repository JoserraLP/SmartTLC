import optparse
import random

from tl_predictor.generators.flows_generator import FlowsGenerator
from tl_predictor.generators.sumo_config_generator import SumoConfigGenerator
from tl_predictor.generators.tl_program_generator import TrafficLightProgramGenerator
from tl_predictor.generators.time_pattern_generator import TimePatternGenerator
from tl_predictor.static.constants import FLOWS_VALUES, DEFAULT_GENERATED_CALENDAR_FILE

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def get_options():
    """
    Define options for the executable script.

    :return: options
    :rtype: object
    """
    optParser = optparse.OptionParser()
    optParser.add_option("-t", "--tl-program-file", dest="tl_program_file", action='store',
                         help="sumo traffic lights programs file location")
    optParser.add_option("-s", "--sumo-config-file", dest="sumo_config_file", action='store',
                         help="sumo configuration file location")
    optParser.add_option("-f", "--flows-config-file", dest="flows_config_file", action='store',
                         help="flow configuration file")
    optParser.add_option("-c", "--calendar", dest="calendar_file", action='store',
                         help="calendar file")
    options, args = optParser.parse_args()
    return options


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

        sumo_config_generator.set_input_files(input_files)

        # Define simulation begin time
        sumo_config_generator.set_begin_time(0)

        # Define the report policy
        policy = {'verbose': 'true', 'no-step-log': 'true'}

        sumo_config_generator.set_report_policy(policy)

        # Save the programs into an output file
        sumo_config_generator.write_output_file(exec_options.sumo_config_file)

    # Generate SUMO config file
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
        time_pattern_generator = TimePatternGenerator(input_file=exec_options.calendar_file)

        time_pattern_generator.parse_calendar()

        pattern_calendar = time_pattern_generator.get_pattern_calendar()

        random_pattern_calendar = time_pattern_generator.get_random_pattern_calendar()

        # Store one month only
        # random_pattern_calendar.loc[0:1487].to_csv(DEFAULT_GENERATED_CALENDAR_FILE, index=False)

        # Store all the year
        random_pattern_calendar.to_csv(DEFAULT_GENERATED_CALENDAR_FILE, index=False)

        print(pd.concat([pattern_calendar, random_pattern_calendar]).drop_duplicates(keep=False).reset_index(drop=True))

        '''
        pattern_calendar.traffic_type.value_counts().plot(kind='bar')
        plt.show()

        random_pattern_calendar.traffic_type.value_counts().plot(kind='bar')
        plt.show()
        '''

        '''
        random_pattern_calendar.loc[0:960].reset_index().plot(x='index', y='traffic_type')
        plt.show()
        '''

