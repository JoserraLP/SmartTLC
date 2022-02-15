import optparse

from tl_controller.generators.sumo_config_generator import SumoConfigGenerator
from tl_controller.generators.tl_program_generator import TrafficLightProgramGenerator
import math

from tl_controller.static.constants import LOWER_BOUND_TIME_PHASE, UPPER_BOUND_TIME_PHASE, MAXIMUM_TIME_BOUND_PHASE, \
    MAXIMUM_TIME_PHASE, TRAFFIC_PROPORTIONS, MAXIMUM_TIME_PHASE_TURN


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
    optParser.add_option("-d", "--topology-dim", dest="topology_dim", action='store',
                         help="network topology dimension")
    optParser.add_option("--allow-turns", dest="allow_turns", action='store_true',
                         help="allow turns in traffic lights")
    optParser.add_option("-i", "--interval", dest="interval", action='store',
                         help="interval of seconds to be used in the traffic light generator")
    optParser.add_option("-p", "--proportion", dest="proportion", action='store_true',
                         help="proportions used in the traffic light generator")
    options, args = optParser.parse_args()
    return options


if __name__ == "__main__":
    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Generate TL program file
    if exec_options.tl_program_file:

        # Store the default value or specified one
        if exec_options.topology_dim:
            topology_dim = int(exec_options.topology_dim)
        else:
            # Default to 1
            topology_dim = 1

        # Define the generator
        tl_generator = TrafficLightProgramGenerator(topology_dim)

        if exec_options.allow_turns:
            # Create turn static schema
            # TODO make it clockwise, now it is only contrary directions
            static_schema = [{"duration": "", "state": "GGggrrrrGGggrrrr"},
                             {"duration": "5", "state": "yyggrrrryyggrrrr"},
                             {"duration": "5", "state": "rrGGrrrrrrGGrrrr"},
                             {"duration": "5", "state": "rryyrrrrrryyrrrr"},
                             {"duration": "", "state": "rrrrGGggrrrrGGgg"},
                             {"duration": "5", "state": "rrrryyggrrrryygg"},
                             {"duration": "5", "state": "rrrrrrGGrrrrrrGG"},
                             {"duration": "5", "state": "rrrrrryyrrrrrryy"}]

            maximum_time_phase = MAXIMUM_TIME_PHASE_TURN

            duration_indexes = [0, 4]

        else:
            # Create the basic static schema
            static_schema = [{"duration": "", "state": "GGrrGGrr"},
                             {"duration": "5", "state": "yyrryyrr"},
                             {"duration": "", "state": "rrGGrrGG"},
                             {"duration": "5", "state": "rryyrryy"}]

            maximum_time_phase = MAXIMUM_TIME_PHASE

            duration_indexes = [0, 2]

        # Create the static phases
        if exec_options.proportion:
            for i in range(0, len(TRAFFIC_PROPORTIONS)):
                # Calculate the time on EW direction by proportion
                time_ew = maximum_time_phase / (TRAFFIC_PROPORTIONS[i] + 1)

                # Store both duration values (NS and EW)
                static_schema[duration_indexes[0]]['duration'] = str(math.floor(maximum_time_phase - time_ew))
                static_schema[duration_indexes[1]]['duration'] = str(math.ceil(time_ew))
                # Add the program to the generator
                tl_generator.add_static_program(static_schema, "static_program_{}".format(i+1))
        else:
            # TODO not added turns in this case as it is not used
            interval = int(exec_options.interval)
            # Iterate over the number of intervals
            for i in range(0, int(MAXIMUM_TIME_BOUND_PHASE / interval) + 1):
                # Store both duration values (NS and EW)
                static_schema[0]['duration'] = str(LOWER_BOUND_TIME_PHASE + i * interval)
                static_schema[2]['duration'] = str(UPPER_BOUND_TIME_PHASE - i * interval)
                # Add the program to the generator
                tl_generator.add_static_program(static_schema, "static_program_{}".format(i+1))

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
