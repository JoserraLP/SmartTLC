import argparse

from docker_generator.generator.docker_compose_generator import DockerComposeGenerator
from docker_generator.utils.docker_structure import ALL_CONTAINERS

DEFAULT_OUTPUT_DIRECTORY = './docker_compose.yml'


def get_options():
    """
    Get options from the execution command

    :return: Arguments options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Script that generates a docker-compose.yml specification file, '
                                                     'based on the argument\'s specified containers.')

    # Define the arguments options
    arg_parser.add_argument('-o', '--output-dir', dest='output', action='store',
                            default=DEFAULT_OUTPUT_DIRECTORY, type=str,
                            help='define the output directory where the output file will be stored. '
                                 f'Default is {DEFAULT_OUTPUT_DIRECTORY}.')

    arg_parser.add_argument('-c', '--containers', dest='containers', action='store',
                            default=ALL_CONTAINERS.keys(), type=str, help='containers to be generated on the Docker '
                                                                          'specification files, split by comma ",". '
                                                                          f'Default values are: '
                                                                          f'{",".join(list(ALL_CONTAINERS.keys()))}')

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == '__main__':

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Define the Docker Compose Generator
    docker_generator = DockerComposeGenerator()

    # Generate the containers' connections list
    docker_generator.generate_container_connections_matrix()

    # Parse the containers list
    if ',' in exec_options.containers:
        containers = exec_options.containers.split(',')
    else:
        containers = exec_options.containers

    # Generate the containers file at the given output directory
    docker_generator.generate_containers(output_file=exec_options.output, containers=containers)
