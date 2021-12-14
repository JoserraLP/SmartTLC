import numpy as np


class DependenciesGraph:
    """
    Represents the matrix graph that will store the relation between different containers

    :param num_containers: Number of possible containers
    :type num_containers: int
    """

    def __init__(self, num_containers):
        # Initialize the maximum graph size
        self._max_graph_size = num_containers
        # Create numpy array and initialize it to 0
        self._graph = np.zeros((self._max_graph_size, self._max_graph_size))
        # Set diagonal to -1
        np.fill_diagonal(self._graph, -1)

    @property
    def graph(self):
        """
        Graph getter
        :return: graph matrix
        """
        return self._graph

    @graph.setter
    def graph(self, items):
        """
        Graph setter
        :param items: Matrix with the items that has links or dependencies
        :return: None
        """
        # Items will be a matrix with the items that has links or dependencies
        self._graph = np.add(self._graph, items)
