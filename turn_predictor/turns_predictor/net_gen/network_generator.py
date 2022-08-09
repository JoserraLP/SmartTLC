import numpy as np


def create_matrix(rows: int, cols: int) -> np.ndarray:
    """
    Creates the network topology matrix

    :param rows: matrix topology rows
    :type rows: int
    :param cols: matrix topology cols
    :type cols: int
    :return: network matrix
    :rtype: numpy ndarray
    """
    # Define the matrix as a 1's matrix
    matrix = np.ones((rows, cols), dtype='U5')  # Full string

    # Retrieve corners
    corners = [(0, 0), (0, cols - 1), (rows - 1, 0), (rows - 1, cols - 1)]

    # Retrieve corner positions at rows and cols
    ext_rows, ext_cols = zip(*corners)

    # Set corner values to 0
    matrix[ext_rows, ext_cols] = '0'

    # Define initial ids
    c_id, n_id, w_id, e_id, s_id = 1, 1, 1, 1, 1

    # Iterate over the matrix
    for row in range(rows):
        for col in range(cols):
            # Discord the corners
            if (row == 0 and col == 0) or \
                    (row == rows - 1 and col == 0) or \
                    (row == 0 and col == cols - 1) or \
                    (row == rows - 1 and col == cols - 1):
                continue
            elif row == 0:  # North
                matrix[row][col] = f'n{n_id}'
                n_id += 1
            elif row == rows - 1:  # South
                matrix[row][col] = f's{s_id}'
                s_id += 1
            elif col == 0:  # West
                matrix[row][col] = f'w{w_id}'
                w_id += 1
            elif col == cols - 1:  # East
                matrix[row][col] = f'e{e_id}'
                e_id += 1
            else:
                matrix[row][col] = f'c{c_id}'
                c_id += 1
    return matrix


def generate_roads_list(rows: int, cols: int) -> list:
    """
    Generates a list of all the edges (roads) of the topology.
    
    :param rows: matrix topology rows
    :type rows: int
    :param cols: matrix topology cols
    :type cols: int
    :return: list of all the roads
    :rtype: list
    """
    # Create the network matrix
    matrix = create_matrix(rows=rows, cols=cols)

    # Define the roads list
    all_roads = []

    # Iterate over the matrix
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            # If the matrix cell is valid, get the roads info
            if matrix[row][col] != '0':
                # Retrieve the node identifier
                node_id = matrix[row][col]

                # EDGES
                all_roads += get_roads_by_node(matrix, node_id=node_id, row=row, col=col)

    return all_roads


def get_roads_by_node(matrix: np.ndarray, node_id: str, row: int, col: int) -> list:
    """
    Get roads names given a node.

    :param matrix: network topology matrix.
    :type matrix: numpy ndarray
    :param node_id: node identifier.
    :type node_id: str
    :param row: actual topology row
    :type row: int
    :param col: actual topology column.
    :type col: int
    :return: all the roads of a given node
    :rtype: list
    """

    # Define the roads list and the closest center node identifier
    roads, closest_center_id = [], ""

    # Retrieve closest center node identifier depending on the node id
    if 'n' in node_id:
        closest_center_id = matrix[row + 1][col]
    elif 's' in node_id:
        closest_center_id = matrix[row - 1][col]
    elif 'e' in node_id:
        closest_center_id = matrix[row][col - 1]
    elif 'w' in node_id:
        closest_center_id = matrix[row][col + 1]
    elif 'c' in node_id:
        # The center nodes will be different, as they might check close center connections too
        # Right node
        right_closest_id = matrix[row][col + 1]
        if 'c' in right_closest_id:

            roads.append(node_id + "_" + right_closest_id)
            roads.append(right_closest_id + "_" + node_id)

        # Below node
        below_closest_id = matrix[row + 1][col]
        if 'c' in below_closest_id:
            roads.append(node_id + "_" + below_closest_id)
            roads.append(below_closest_id + "_" + node_id)

    # If there are close center node, store the from and to nodes and the priority
    if closest_center_id:
        roads.append(node_id + "_" + closest_center_id)
        roads.append(closest_center_id + "_" + node_id)

    return roads
