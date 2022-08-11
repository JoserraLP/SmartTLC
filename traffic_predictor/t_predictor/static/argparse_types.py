import argparse
import os


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

    if len(prediction_info.split(',')) != 5 or len(prediction_info.split(',')) != 7:
        raise argparse.ArgumentTypeError('Invalid value. Please, use the following format: road,hour,date_day,'
                                         'date_month,date_year.')
    return prediction_info
