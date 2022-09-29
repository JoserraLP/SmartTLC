import argparse
import os


def check_dimension(dimension: str) -> int:
    """
    Check if the dimension of the argument is valid

    :param dimension: matrix dimension
    :type dimension: str
    :return: dimension if valid
    :rtype: int
    """
    # Parse to int
    dim = int(dimension)

    if dim < 1:
        raise argparse.ArgumentTypeError('Invalid value. Minimum dimension is 1')
    return dim


def check_greater_zero(argument: str) -> int:
    """
    Check if the argument is greater than zero

    :param argument: argument value
    :type argument: str
    :return: lanes if valid
    :rtype: int
    """
    # Parse to int
    argument = int(argument)

    if argument <= 0:
        raise argparse.ArgumentTypeError('Invalid value. Minimum value is 1')
    return argument


def check_valid_junction_type(junction_type: str) -> str:
    """
    Check if the junction type of the argument is valid

    :param junction_type: junction type
    :type junction_type: str
    :return: junction type if valid
    :rtype: str
    """

    if junction_type not in ["priority", "traffic_light", "right_before_left", "priority_stop", "allway_stop",
                             "traffic_light_right_on_red"]:
        raise argparse.ArgumentTypeError('Invalid value. Possible values are: "priority", "traffic_light", '
                                         '"right_before_left", "priority_stop", "allway_stop", '
                                         '"traffic_light_right_on_red"')
    return junction_type


def check_valid_tl_type(tl_type: str) -> str:
    """
    Check if the traffic light type of the argument is valid

    :param tl_type: traffic light type
    :type tl_type: str
    :return: traffic light type if valid
    :rtype: str
    """

    if tl_type not in ["static", "actuated", "delay_based"]:
        raise argparse.ArgumentTypeError('Invalid value. Possible values are: "static", "actuated", "delay_based"')
    return tl_type


def check_valid_tl_layout(tl_layout: str) -> str:
    """
    Check if the traffic light layout of the argument is valid

    :param tl_layout: traffic light layout
    :type tl_layout: str
    :return: traffic light layout
    :rtype: str
    """

    if tl_layout not in ["opposites", "incoming", "alternateOneWay"]:
        raise argparse.ArgumentTypeError('Invalid value. Possible values are: "opposites", "incoming", '
                                         '"alternateOneWay"')
    return tl_layout


def check_file(file_dir: str) -> str:
    """
    Check if the file exists
    :param file_dir: file directory
    :type file_dir: str
    :return: file_dir
    :rtype: str
    """
    if not os.path.exists(file_dir):
        raise argparse.ArgumentTypeError(f'Invalid value. File {file_dir} does not exist.')
    return file_dir
