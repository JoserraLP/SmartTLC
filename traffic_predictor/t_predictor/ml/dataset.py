import pandas as pd
from sklearn.model_selection import KFold, train_test_split
from t_predictor.ml.utils import drop_nan_values, parse_str_features, check_dataset_bias
from t_predictor.static.constants import DEFAULT_OUTPUT_FILE


class SimulationDataset:

    def __init__(self, file_dir: str = DEFAULT_OUTPUT_FILE):
        """
        SimulationDataset class initializer.

        :param file_dir: directory where the time pattern is located.
        :type file_dir: str
        :return None
        """
        self._dataset = pd.read_csv(file_dir)

        valid_target_values = [i for i in range(len(list(self._dataset.columns))) if i != 1]

        # Define input and target values
        # Relevant values
        self._features_values = self._dataset.iloc[0:, valid_target_values]
        # Traffic type
        self._target_values = self._dataset.iloc[0:, 1].to_frame()

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
        # Create a k_fold instance
        k_fold = KFold(n_splits=k, shuffle=True, random_state=random_state)

        # Create a dict to store the datasets
        k_fold_datasets = []

        # Iterate over k_fold splits
        for train_index, test_index in k_fold.split(X=self._features_values):

            # Get the X and y datasets
            x_train, x_test = self._features_values.iloc[train_index], self._features_values.iloc[test_index]
            y_train, y_test = self._target_values.iloc[train_index], self._target_values.iloc[test_index]

            # Append the datasets to the list
            k_fold_datasets.append({'X_train': x_train, 'X_test': x_test, 'y_train': y_train, 'y_test': y_test})

        return k_fold_datasets
