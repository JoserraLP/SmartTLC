import optparse

from tl_study.generators.tl_program_generator import TrafficLightProgramGenerator


def get_options():
    """
    Define options for the executable script.

    :return: options
    :rtype: object
    """
    optParser = optparse.OptionParser()
    optParser.add_option("-t", "--tl-program-file", dest="tl_program_file", action='store',
                         help="sumo traffic lights programs file location")
    options, args = optParser.parse_args()
    return options


if __name__ == "__main__":
    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Generate TL program file
    if exec_options.tl_program_file:
        # Define the generator
        tl_generator = TrafficLightProgramGenerator()

        # Create the basic static schema
        static_schema = [{"duration": "", "state": "GGrrGGrr"},
                         {"duration": "5", "state": "yyrryyrr"},
                         {"duration": "", "state": "rrGGrrGG"},
                         {"duration": "5", "state": "rryyrryy"}]

        # Create the static phases
        for i in range(0, 13):
            static_schema[0]['duration'] = str(10 + i*5)
            static_schema[2]['duration'] = str(70 - i*5)
            tl_generator.add_static_program(static_schema, f'static_program_{i+1}')

        # Save the programs into an output file
        tl_generator.write_output_file(exec_options.tl_program_file)
