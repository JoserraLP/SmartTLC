import numpy as np


class DependenciesGraph:
    """
    Represents the matrix graph that will store the relation between different containers

    Attributes:

    - max_graph_size (int): maximum size of the graph
    - graph (numpy ndarray): dependencies graph represented as a matrix

    :param num_containers: number of possible containers
    :type num_containers: int
    """

    def __init__(self, num_containers: int):
        # Create numpy array and initialize it to 0
        self._graph = np.zeros((num_containers, num_containers))
        # Set diagonal to -1
        np.fill_diagonal(self._graph, -1)

    @property
    def graph(self) -> np.ndarray:
        """
        Graph getter

        :return: graph matrix
        :rtype: numpy ndarray
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
