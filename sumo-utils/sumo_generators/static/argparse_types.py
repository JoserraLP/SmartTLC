import argparse


def check_dimension(dimension):
    """
    Check if the dimension of the argument is valid
    :param dimension: matrix dimension
    :type dimension: int
    :return: dimension
    """
    dim = int(dimension)

    if dim < 3:
        raise argparse.ArgumentTypeError('Invalid value. Minimum dimension is 3')
    return dim


def check_valid_junction_type(junction_type):
    """
    Check if the junction type of the argument is valid
    :param junction_type: junction type
    :type junction_type: str
    :return: dimension
    """

    if junction_type not in ["priority", "traffic_light", "right_before_left", "priority_stop", "allway_stop",
                         "traffic_light_right_on_red"]:
        raise argparse.ArgumentTypeError('Invalid value. Possible values are: "priority", "traffic_light", '
                                         '"right_before_left", "priority_stop", "allway_stop", '
                                         '"traffic_light_right_on_red"')
    return junction_type


def check_valid_tl_type(tl_type):
    """
    Check if the traffic light type of the argument is valid
    :param tl_type: traffic light type
    :type tl_type: str
    :return: tl_type
    """

    if tl_type not in ["static", "actuated", "delay_based"]:
        raise argparse.ArgumentTypeError('Invalid value. Possible values are: "static", "actuated", "delay_based"')
    return tl_type


def check_valid_tl_layout(tl_layout):
    """
    Check if the traffic light layout of the argument is valid
    :param tl_layout: traffic light layout
    :type tl_layout: str
    :return: tl_layout
    """

    if tl_layout not in ["opposites", "incoming", "alternateOneWay"]:
        raise argparse.ArgumentTypeError('Invalid value. Possible values are: "opposites", "incoming", '
                                         '"alternateOneWay"')
    return tl_layout
