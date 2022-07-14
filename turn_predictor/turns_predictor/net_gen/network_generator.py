import numpy as np


def generate_node_list(rows, cols):
    # Define the matrix
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

    all_edges = []

    # Iterate over the matrix
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            # If the matrix cell is valid, generate the node and edges
            if matrix[row][col] != '0':
                # Retrieve the node identifier
                node_id = matrix[row][col]

                # EDGES
                all_edges += generate_edges(matrix, node_id=node_id, row=row, col=col)

    return all_edges


def generate_edges(matrix, node_id, row, col):
    edges = []
    # Define the edges string and the closest center node identifier
    closest_center_id = ""

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

            edges.append(node_id + "_" + right_closest_id)
            edges.append(right_closest_id + "_" + node_id)

        # Below node
        below_closest_id = matrix[row + 1][col]
        if 'c' in below_closest_id:
            edges.append(node_id + "_" + below_closest_id)
            edges.append(below_closest_id + "_" + node_id)

    # If there are close center node, store the from and to nodes and the priority
    if closest_center_id:
        edges.append(node_id + "_" + closest_center_id)
        edges.append(closest_center_id + "_" + node_id)

    return edges
