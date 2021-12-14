import optparse

from docker_compose_generator import DockerGenerator
from docker_structure import ALL_CONTAINERS


def get_options():
    """
    Get options from the execution command
    :return: Arguments options
    """
    # Create the Option Parser
    optParser = optparse.OptionParser()

    # Define the arguments options
    optParser.add_option("-o", "--output-dir", dest="output", action="store",
                         default="./docker_compose.yml", type="string",
                         help="define the output directory where the 'docker-compose.yml' will be stored")
    optParser.add_option("-c", "--containers", dest="containers", action='store',
                         default=ALL_CONTAINERS.keys(), type="string", help="sumo configuration file location")

    # Retrieve the arguments parsed
    options, args = optParser.parse_args()
    return options


if __name__ == '__main__':

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Define the Docker Generator
    docker_generator = DockerGenerator()

    # Generate the containers' connections list
    docker_generator.generate_connections_list()

    # Parse the containers list
    if type(exec_options.containers) == str:
        containers = exec_options.containers.split(',')
    else:
        containers = exec_options.containers

    # Generate the containers file at the given output directory
    docker_generator.generate_containers(output_file=exec_options.output, containers=containers)
