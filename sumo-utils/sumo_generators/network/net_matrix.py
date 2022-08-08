import numpy as np

from sumo_generators.static.constants import *


class NetMatrix:
    """
    Class representing the network matrix

    :param num_rows: number of matrix rows
    :type num_rows: int
    :param num_cols: number of matrix cols
    :type num_cols: int
    """

    def __init__(self, num_rows: int = MIN_ROWS, num_cols: int = MIN_COLS):
        # Define the number of rows and columns of the matrix
        self._num_rows = num_rows
        self._num_cols = num_cols

        # Define the matrix as a 1's matrix
        self._matrix = np.ones((num_rows, num_cols), dtype='U5')  # Full string

    def generate_connections_matrix(self) -> np.ndarray:
        """
        Generate connections matrix, setting the ids for each node and 0 to the corners

        :return: connections matrix
        :rtype: numpy ndarray
        """
        # Retrieve corners
        corners = [(0, 0), (0, self._num_cols - 1), (self._num_rows - 1, 0), (self._num_rows - 1, self._num_cols - 1)]

        # Retrieve corner positions at rows and cols
        rows, cols = zip(*corners)

        # Set corner values to 0
        self._matrix[rows, cols] = '0'

        # Generate nodes ids
        self.generate_nodes_id()

        return self._matrix

    def generate_nodes_id(self) -> None:
        """
        Generate nodes ids and store them into the matrix

        :return: None
        """
        # Define initial ids
        c_id, n_id, w_id, e_id, s_id = 1, 1, 1, 1, 1

        # Iterate over the matrix
        for row in range(self._num_rows):
            for col in range(self._num_cols):
                # Discord the corners
                if (row == 0 and col == 0) or \
                        (row == self._num_rows - 1 and col == 0) or \
                        (row == 0 and col == self._num_cols - 1) or \
                        (row == self._num_rows - 1 and col == self._num_cols - 1):
                    continue
                elif row == 0:  # North
                    self._matrix[row][col] = f'n{n_id}'
                    n_id += 1
                elif row == self._num_rows - 1:  # South
                    self._matrix[row][col] = f's{s_id}'
                    s_id += 1
                elif col == 0:  # West
                    self._matrix[row][col] = f'w{w_id}'
                    w_id += 1
                elif col == self._num_cols - 1:  # East
                    self._matrix[row][col] = f'e{e_id}'
                    e_id += 1
                else:
                    self._matrix[row][col] = f'c{c_id}'
                    c_id += 1

    @property
    def matrix(self) -> np.ndarray:
        """
        Getter of the connection matrix

        :return: connection matrix
        :rtype: numpy ndarray
        """
        return self._matrix

    @matrix.setter
    def matrix(self, matrix) -> None:
        """
        Setter of the connection matrix

        :param matrix: connection matrix
        :return: None
        """
        self._matrix = matrix
