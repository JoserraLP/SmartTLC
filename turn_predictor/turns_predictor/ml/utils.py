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


def drop_nan_values(dataset: pd.DataFrame) -> None:
    """
    Drop NaN values of the dataset

    :param dataset: dataset where the data will be dropped
    :type dataset: DataFrame
    :return: None
    """
    # Drop the rows with NaN values
    dataset.dropna(axis=0)


def parse_str_features(dataset: pd.DataFrame) -> dict:
    """
    Parse the string features to int values

    :param dataset: dataset where the data will be replaced
    :type dataset: DataFrame
    :return: parsed values dictionary
    :rtype: dict
    """
    # Create dict to store all features parsed values
    features_parsed_values = {}

    # Create a list with the features with a "object" value = str object
    features = list(dataset.select_dtypes(include='object').columns)

    # Iterate over the features
    for feature in features:

        # Get unique values of the feature in a dict starting at 1
        feature_values = dict(enumerate(dataset[feature].unique().flatten(), 1))

        # Store the values in the features_parsed_values dict
        features_parsed_values[feature] = feature_values

        # Parse the data from string to int value with the previous created dict
        for k, v in feature_values.items():
            dataset[feature] = dataset[feature].replace([v], k)

    return features_parsed_values


def check_dataset_bias(dataset: pd.DataFrame, field: str, bias: float = 30.0) -> bool:
    """
    Check if a given dataset is biased on a given feature.

    :param dataset: DataFrame of the dataset
    :type dataset: DataFrame
    :param field: field to check bias
    :type field: str
    :param bias: bias threshold. Default to 30.0
    :type bias: float
    :return: True if the dataset is biased, False if not
    :rtype: bool
    """
    # Numpy array of percentages
    percentages = np.array([])

    try:
        # Iterate over the field
        for field_val in dataset[field].unique():
            # Get number of maps values and percentage
            field_values = dataset[dataset[field] == field_val].shape[0]
            field_percentage = field_values / dataset[field].shape[0] * 100

            '''
            print(f"### Field {field_val} ###")
            print(f"The number of values is \033[1m{field_values}\033[0m")
            print(f"Percentage of the field is \033[1m{field_percentage}\033[0m %")
            '''

            # Append to the numpy array
            percentages = np.append(percentages, field_percentage)

    except Exception as e:
        print(e)
        return None

    # Return boolean indicating either the dataset is biased on the map feature or not. For example 30% of difference
    return np.max(np.abs(np.diff(percentages))) > bias
