import pandas as pd

import numpy as np

from t_predictor.static.constants import DEFAULT_OUTPUT_FILE
from sklearn.model_selection import KFold, train_test_split


def drop_nan_values(dataset: pd.DataFrame) -> None:
    """
    Replace the NaN values indicated by parameters with its mean.

    :param dataset: dataset where the data will be replaced
    :type dataset: DataFrame
    :return: Non
    """
    # Drop the rows with NaN values
    dataset.dropna(axis=0)


def parse_str_features(dataset: pd.DataFrame) -> dict:
    """
    Parse the string features to int values

    :param dataset: dataset where the data will be replaced
    :type dataset: DataFrame
    """
    # Create dict to store all features parsed values
    features_parsed_values = {}

    # Create a list with the features with a "object" value = str object
    features = list(dataset.select_dtypes(include='object').columns)

    # Iterate over the features
    for feature in features:

        # Get unique values of the feature in a dict
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
    :param bias:  bias threshold
    :type bias: float
    :return True if the dataset is biased, False if not
    :rtype bool
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


class SimulationDataset:

    def __init__(self, file_dir: str = DEFAULT_OUTPUT_FILE, date: bool = False):
        """
        SimulationDataset class initializer.

        :param file_dir: directory where the time pattern is located. Default to simulation_month.csv
        :type file_dir: str
        :param date: if True train models based on date only, otherwise with contextual information too.
            Default to True.
        :type date: bool
        :return None
        """
        self._dataset = pd.read_csv(file_dir)

        # Define input and target values
        # Relevant values
        if date: # If date train, retrieve only those values
            self._features_values = self._dataset.iloc[0:, 6:]
        else: # Otherwise retrieve all the values
            self._features_values = self._dataset.iloc[0:, 4:]
        # Traffic type
        self._target_values = self._dataset.iloc[0:, 3].to_frame()

    def get_dimensions(self):
        """
        Get the dimensions of the dataset.

        :return: a tuple with the number of rows and columns of the dataset
        :rtype: tuple
        """
        return self._dataset.shape

    @property
    def features_values(self):
        """
        Get the input features and its values.

        :return: DataFrame with the input features labels and values
        :rtype: DataFrame
        """
        return self._features_values

    @property
    def target_values(self):
        """
        Get the target feature ('traffic_type') and its values.

        :return: DataFrame with the target feature labels and values
        :rtype: DataFrame
        """
        return self._target_values

    def clean_up_dataset(self):
        # 1. Check the NaN values of both datasets
        features_nan_values = self._features_values.isnull().sum().sum()
        target_nan_values = self._target_values.isnull().sum().sum()

        # 2. Drop rows with NaN values on both datasets
        if features_nan_values > 0:
            drop_nan_values(self._features_values)

        if target_nan_values > 0:
            drop_nan_values(self._target_values)

        # 3. Parse str values to int on both datasets
        features_parsed_dict = parse_str_features(self._features_values)
        target_parsed_dict = parse_str_features(self._target_values)

        # Merge both dicts
        parsed_values_dict = features_parsed_dict
        parsed_values_dict.update(target_parsed_dict)

        # 4. Check if dataset is biased
        is_target_biased = check_dataset_bias(self._target_values, 'traffic_type', bias=40)

        # Show a message if it is biased
        if is_target_biased:
            print("The dataset is biased on the traffic type")

        return parsed_values_dict

    def train_test_split(self, train_percentage: float = 0.70, test_percentage: float = 0.30, random_state: int = 42,
                         shuffle: bool = True):
        """
        Perform the train test split and return the datasets

        :param train_percentage: percentage of the dataset that will be used for training. Default to 0.70.
        :type train_percentage: float
        :param test_percentage: percentage of the dataset that will be used for test. Default to 0.30
        :type test_percentage: float
        :param random_state: random state for the split.
        :type random_state: int
        :param shuffle: flag to shuffle the data.
        :type shuffle: bool
        :return: list of datasets split by the basic train-test split (x_train, x_test, y_train, y_test)
        :rtype list
        """
        return train_test_split(self._features_values, self._target_values, train_size=train_percentage,
                                test_size=test_percentage, random_state=random_state, shuffle=shuffle)

    def k_fold_split(self, k: int = 10, random_state: int = 1):
        """
        Perform the K-Fold split and return the datasets

        :param k: number of splits. Default to 10.
        :type k: int
        :param random_state: random seed. Default to 1.
        :type random_state: int
        :return: list of datasets split by the k-fold process
        :rtype list
        """
        # Create a kfold instance
        kfold = KFold(n_splits=k, shuffle=True, random_state=random_state)

        # Create a dict to store the datasets
        kfold_datasets = []

        # Iterate over kfold splits
        for train_index, test_index in kfold.split(X=self._features_values):

            # Get the X and y datasets
            X_train, X_test = self._features_values.iloc[train_index], self._features_values.iloc[test_index]
            y_train, y_test = self._target_values.iloc[train_index], self._target_values.iloc[test_index]

            # Append the datasets to the list
            kfold_datasets.append({'X_train': X_train, 'X_test': X_test, 'y_train': y_train, 'y_test': y_test})

        return kfold_datasets
