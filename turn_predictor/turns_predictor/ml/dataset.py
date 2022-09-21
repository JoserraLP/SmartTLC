import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, train_test_split
from turns_predictor.ml.utils import drop_nan_values, parse_str_features
from turns_predictor.net_gen.network_generator import generate_roads_list
from sumo_generators.static.constants import DEFAULT_TURN_DICT


class TurnDataset:
    """
    TurnDataset class.
    
    :param file_dir: directory where the time pattern is located. Default to current directory
    :type file_dir: str
    :param cols: network topology columns. Default to -1.
    :type cols: int
    :param rows: network topology rows. Default to -1.
    :type rows: int
    :return: None
    """

    def __init__(self, file_dir: str = '.', cols: int = -1, rows: int = -1):
        """
        TurnDataset class initializer.
        """
        # Load the dataset from the time pattern file 
        self._dataset = pd.read_csv(file_dir)

        # Generate roads -> Added 2 because of the external nodes
        self._topology_roads = generate_roads_list(rows=rows + 2, cols=cols + 2)

        # Update the dataset to store the road, date info and turn probabilities in a valid format
        self._dataset = self.process_dataset_info()

        # Define features and target values
        # Road, date_year, date_month, date_day and hour
        self._features_values = self._dataset.iloc[0:, 0:5]

        # Turn probabilities
        self._target_values = self._dataset.iloc[0:, 5:]

    @property
    def features_values(self) -> pd.DataFrame:
        """
        Get the input features and its values.

        :return: DataFrame with the input features labels and values
        :rtype: DataFrame
        """
        return self._features_values

    @property
    def target_values(self) -> pd.DataFrame:
        """
        Get the target feature ('traffic_type') and its values.

        :return: DataFrame with the target feature labels and values
        :rtype: DataFrame
        """
        return self._target_values

    def clean_up_dataset(self) -> dict:
        """
        Clean up the dataset by performing the following steps on both features and target datasets:

        1. Check NaN values.
        2. Drop rows with NaN values.
        3. Parse str values to int.
        4. Store parsed values.

        :return: parsed values dictionary.
        :rtype: dict.
        """
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

        return parsed_values_dict

    def process_dataset_info(self) -> pd.DataFrame:
        """
        Process the turn pattern information in order to achieve a valid training format with the values specified. 
        The resulting dataset will have the following fields: road, date_year, date_month, date_day, hour, 
        turn_right, turn_left, turn_forward.
        
        :return: processed dataset
        :rtype: pd.DataFrame
        """

        # Create a numpy array with the required columns and its types
        dtypes = np.dtype(
            [
                ("road", str),
                ("date_year", int),
                ("date_month", int),
                ("date_day", int),
                ("hour", str),
                ("turn_right", float),
                ("turn_left", float),
                ("turn_forward", float),
            ]
        )

        # Create an empty DataFrame with the columns
        processed_dataset = pd.DataFrame(np.empty(0, dtype=dtypes))

        # Iterate over each row to retrieve road turns information
        for index, row in self._dataset.iterrows():
            # Check if there is specified more than one road.
            if ';' in row['road']:
                # Retrieve information related to the turns and the roads specified
                turn_right, turn_left, turn_forward, turn_roads = row['turn_right'].split(';'), \
                                                                  row['turn_left'].split(';'), \
                                                                  row['turn_forward'].split(';'), \
                                                                  row['road'].split(';')
            # Otherwise it means all the roads have the same probabilities
            else:
                # Retrieve information related to the turns of all roads and set turn_roads to None
                turn_right, turn_left, turn_forward, turn_roads = float(row['turn_right']), float(row['turn_left']), \
                                                                  float(row['turn_forward']), None

            # Iterate over all the topology roads
            for road in self._topology_roads:
                # Create road info schema
                road_info = {
                    'road': road, 'date_year': int(row['date_year']), 'date_month': int(row['date_month']),
                    'date_day': int(row['date_day']), 'hour': row['hour'], 'turn_right': 0.0,
                    'turn_left': 0.0, 'turn_forward': 0.0
                }
                # All the roads have the same probability
                if row['road'] == 'all':
                    road_info['turn_right'] = turn_right
                    road_info['turn_left'] = turn_left
                    road_info['turn_forward'] = turn_forward
                # Retrieve info from dataset if road is specified
                elif turn_roads and road in turn_roads:
                    # Retrieve current road index
                    road_idx = turn_roads.index(road)
                    # Retrieve turn values
                    road_info['turn_right'] = float(turn_right[road_idx])
                    road_info['turn_left'] = float(turn_left[road_idx])
                    road_info['turn_forward'] = float(turn_forward[road_idx])
                # Otherwise use default turn info
                else:
                    road_info['turn_right'] = DEFAULT_TURN_DICT['turn_right']
                    road_info['turn_left'] = DEFAULT_TURN_DICT['turn_left']
                    road_info['turn_forward'] = DEFAULT_TURN_DICT['turn_forward']

                # Store processed info
                processed_dataset = processed_dataset.append(road_info, ignore_index=True)

        return processed_dataset

    def train_test_split(self, train_percentage: float = 0.70, test_percentage: float = 0.30, random_state: int = 42,
                         shuffle: bool = True) -> list:
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

    def k_fold_split(self, k: int = 10, random_state: int = 1) -> list:
        """
        Perform the K-Fold split and return the datasets.

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
