from sklearn.metrics import mean_squared_error, mean_absolute_error

import pickle
import os
import pandas as pd


def check_file_extension(file_dir: str):
    """
    Check file name extension and return it with .pickle if not valid

    :param file_dir: file directory name
    :type file_dir: str
    :return: filename with .pickle extension
    :rtype: str
    """
    # Retrieve filename and extension
    filename, filename_ext = os.path.splitext(file_dir)
    # Parse to a .pickle extension
    if filename_ext == '' or filename_ext != '.pickle':
        filename_ext = '.pickle'

    # Create the new file extension
    return filename + filename_ext


def save_model(model: object, output_dir: str):
    """
    Save model into a given file

    :param model: model instance
    :type model: object
    :param output_dir: output directory to store the model
    :type output_dir: str
    :return: None
    """
    # Check file extension
    output_dir = check_file_extension(output_dir)

    # Open file to dump the model
    f = open(output_dir, 'wb')
    # Dump the model
    pickle.dump(model, f)
    # Close the output file
    f.close()


def load_model(input_dir: str):
    """
    Load model from an directory

    :param input_dir: directory where the model is stored
    :type input_dir: str
    :return: model loaded
    :rtype: object
    """
    # Check input classifier file
    input_dir = check_file_extension(input_dir)
    # Read from input file
    f = open(input_dir, 'rb')
    # Retrieve model
    model = pickle.load(f)
    # Close file
    f.close()
    return model


def calculate_pred_metrics(test_target_dataset: pd.DataFrame, pred_target_dataset: pd.DataFrame):
    """
    Calculate models metrics Mean Squared Error, Root Mean Squared Error, Mean Absolute Error

    :param test_target_dataset: dataframe with test dataset
    :type test_target_dataset: pd.DataFrame
    :param pred_target_dataset: dataframe with predicted dataset
    :type pred_target_dataset: pd.DataFrame

    :return MSE, RMSE and MEA
    """
    # Retrieve MSE, RMSE, MEA
    mse = mean_squared_error(test_target_dataset, pred_target_dataset)
    rmse = mean_squared_error(test_target_dataset, pred_target_dataset, squared=False)
    mea = mean_absolute_error(test_target_dataset, pred_target_dataset)

    return mse, rmse, mea
