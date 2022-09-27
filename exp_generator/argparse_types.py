import argparse
import os
import re


def check_dimension(dimension: int) -> int:
    """
    Check if the dimension of the argument is valid
    :param dimension: matrix dimension
    :type dimension: int
    :return: dimension
    :rtype: int
    """
    dim = int(dimension)

    if dim < 1:
        raise argparse.ArgumentTypeError('Invalid value. Minimum dimension is 1')
    return dim


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


def check_valid_format(date: str) -> str:
    """
    Check if the date follows a valid pattern
    :param date: date interval str
    :type date: str
    :return: date
    :rtype: str
    """
    if not re.fullmatch(r'\d{2}/\d{2}/\d{4}-\d{2}/\d{2}/\d{4}', date):
        raise argparse.ArgumentTypeError(f'Invalid format. Valid format is dd/mm/yyyy-dd/mm/yyyy.')
    return date


def check_valid_predictor_value(value: str) -> str:
    """
    Check if the predictor type value is valid
    :param value: predictor type value
    :type value: str
    :return: value
    :rtype: str
    """
    if value not in ['date', 'context']:
        raise argparse.ArgumentTypeError(f'Invalid value. Possible values are "date" or "context')
    return value
