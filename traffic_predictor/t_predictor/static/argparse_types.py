import argparse
import os

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


def check_valid_prediction_info(prediction_info: str) -> str:
    """
    Check if the prediction info format is valid

    :param prediction_info: traffic type used to predict
    :type prediction_info: str
    :return: junction type if valid
    :rtype: str
    """

    if len(prediction_info.split(',')) != 5:
        raise argparse.ArgumentTypeError('Invalid value. Please, use the following format: hour,date,date_day,'
                                         'date_month,date_year.')
    return prediction_info
