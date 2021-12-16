import numpy as np

from dependencies_graph import DependenciesGraph
from docker_structure import ALL_CONTAINERS, DOCKER_EXECUTION_OPTIONS
from decorators import check_containers


def generate_index_list(data):
    """ Generate a list with the indexes of the input data, compared to the default containers list

    :param data: List with the containers name that are related
    :return: list with the indexes of the containers that exists in the input data
    """
    # Retrieve a list of all the default containers list
    keys, indexes = list(ALL_CONTAINERS.keys()), []
    # If the data is a list process each element
    if type(data) == list:
        for item in data:
            # Retrieve the index of the item
            index = keys.index(item)
            # Check the index is valid and append it
            if index >= 0:
                indexes.append(index)
    else:
        # Retrieve the index of the item
        index = keys.index(data)
        # Check the index is valid and append it
        if index >= 0:
            indexes.append(index)
    # Remove duplicates parsing the list to a set
    return list(set(indexes))


def generate_list_items(field):
    """ Generate a string representing the specific container field information

    :param field:
    :return:
    """
    all_items_str, item_str = '', '      - \"{}\"\n'
    # If the field is a list process each element
    if type(field) == list:
        for item in field:
            all_items_str += item_str.format(item)
    else:
        all_items_str = item_str.format(field)
    return all_items_str


class DockerGenerator:
    """ Class representing the docker-compose file generator
    """

    def __init__(self):
        # Define the global container schema
        self._container_schema = "  {container}:\n" \
                                 "    image: {image}\n" \
                                 "    container_name: {container_name}\n" \
                                 "    restart: {restart}\n" \
                                 "    volumes:\n{volumes}" \
                                 "    networks:\n" \
                                 "      net:\n" \
                                 "        ipv4_address: {ip_address}\n"

        # Define the network schema
        self._network_schema = "networks:\n" \
                               "  net:\n" \
                               "    driver: bridge\n" \
                               "    ipam:\n" \
                               "     config:\n" \
                               "       - subnet: 172.20.0.0/16\n"

        # Retrieve the number of possible containers
        self._num_containers = len(ALL_CONTAINERS.keys())

        # Create the dependencies graph
        self.dependencies = DependenciesGraph(self._num_containers)

    def generate_connections_list(self):
        """ Generate the connections list and store it in the dependencies graph
        """
        # Define the connection matrix as a numpy matrix of zeros
        connections_matrix = np.zeros((self._num_containers, self._num_containers))

        # Define an iterator matrix over the columns
        i = 0
        # Iterate over all the possible containers
        for k, v in ALL_CONTAINERS.items():
            link_indexes, dependencies_indexes = [], []
            # Generate the lists of links and dependencies of the default containers
            if 'links' in v:
                link_indexes = generate_index_list(data=v['links'])
            if 'depends_on' in v:
                dependencies_indexes = generate_index_list(data=v['depends_on'])

            # Merge lists and remove duplicates
            total_indexes = link_indexes + list(set(dependencies_indexes) - set(link_indexes))
            # Append a 1 at a given position indicating that the container appears
            for index in total_indexes:
                connections_matrix[i][index] = 1
            i += 1
        # Store the connections matrix on the dependencies graph
        self.dependencies.graph = connections_matrix

    def generate_container_item(self, container_name: str, container: dict):
        """ Generate the string representing a given container

        :param container_name: Container name
        :type container_name: str
        :param container: Container data
        :type container: dict
        :return:
        """

        # Generate the volumes field
        volumes = generate_list_items(container['volumes'])

        # If the 'build' tag is defined on the container modify the container schema and change the 'image' tag for
        # 'build' and append all the information to it
        if 'build' in container:
            container_str = self._container_schema.replace('image', 'build').format(container=container_name,
                                                                                    build=container['build'],
                                                                                    container_name=container[
                                                                                        'container_name'],
                                                                                    restart=container['restart'],
                                                                                    volumes=volumes,
                                                                                    ip_address=container[
                                                                                        'ipv4_address'])
        # Otherwise, append the information without modifying the container schema
        else:
            container_str = self._container_schema.format(container=container_name, image=container['image'],
                                                          container_name=container['container_name'],
                                                          restart=container['restart'], volumes=volumes,
                                                          ip_address=container['ipv4_address'])

        # Generate the fields for all the possible info in a container (ports, env_file, user, links, depends_on,
        # command and entrypoint). More coming soon.
        if "ports" in container:
            container_str += "    ports:\n{}".format(generate_list_items(container['ports']))
        if "env_file" in container:
            container_str += "    env_file:\n{}".format(generate_list_items(container['env_file']))
        if "user" in container:
            container_str += "    user: \"{}\"\n".format(container['user'])
        if "links" in container:
            container_str += "    links:\n{}".format(generate_list_items(container['links']))
        if "depends_on" in container:
            container_str += "    depends_on:\n{}".format(generate_list_items(container['depends_on']))
        if "command" in container:
            # TODO add execution options to container generator
            # Append execution params for both traffic_light_predictor and traffic_light_controller
            if 'traffic_light_controller' in container_name:
                container_str += "    command: {}\n".format(container['command'].format(
                    DOCKER_EXECUTION_OPTIONS['traffic_light_controller']['monday']))
            else:
                container_str += "    command: {}\n".format(container['command'])
        if "entrypoint" in container:
            container_str += "    entrypoint: {}\n".format(container['entrypoint'])

        return container_str

    @check_containers
    def generate_containers(self, output_file: str, containers: list):
        """ Generate the containers string and store it in the docker-compose file, both specified by params

        :param output_file: Output file where the information will be stored
        :type output_file: str
        :param containers: Selected containers by the user
        :type containers: list
        """

        # Open the output file as write only
        docker_file = open(output_file, 'w')

        # Write meta-data about the file
        docker_file.write("version: \"3.3\"\n")
        docker_file.write("services: \n")

        # Define the generated container list and retrieve all the possible containers keys
        generated_containers, keys = [0] * self._num_containers, list(ALL_CONTAINERS.keys())
        # Define index iterator over generated_containers list
        i = 0

        # Iterate over the possible containers
        for k, v in ALL_CONTAINERS.items():
            # If the container exists in selected containers
            if k in containers:
                # If the containers has not been generated previously
                if generated_containers[i] == 0:

                    # Write the container info into the output file
                    docker_file.write(self.generate_container_item(k, v))

                    # Retrieve connections from the dependencies graph
                    connections = self.dependencies.graph[i]

                    # Iterate over connections
                    for index, connection in enumerate(connections):
                        # If there is a connection and it has not been generated previously
                        if connection == 1 and generated_containers[index] == 0:
                            # Retrieve connected container name and data
                            connection_name = keys[index]
                            connection_value = ALL_CONTAINERS[keys[index]]
                            # Generate container item and write it into the output file
                            docker_file.write(self.generate_container_item(connection_name, connection_value))

                            # Update the flag for generated containers
                            generated_containers[index] = 1

                    # Update the flag for generated containers
                    generated_containers[i] = 1

            # Increase the matrix index
            i += 1

        # Store the network info into the output file
        docker_file.write(self._network_schema)
