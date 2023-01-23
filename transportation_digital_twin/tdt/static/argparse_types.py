import argparse
import os
import re


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
