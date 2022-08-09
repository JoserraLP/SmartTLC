import json

import pandas as pd
from turns_predictor.ml.regression_algorithms import KNearestNeighbors
from turns_predictor.ml.utils import load_model
from turns_predictor.static.constants import MODEL_BASE_DIR, MODEL_PERFORMANCE_FILE, MODEL_PARSED_VALUES_FILE, \
    DEFAULT_NUM_MODELS


def sort_performances(performances: list) -> list:
    """
    Sort the performances list by the 'mse' field.

    :param performances: list with model's performances.
    :type performances: list
    :return: sorted list
    :rtype: list
    """
    return sorted(performances, key=lambda x: x['mse'])


class ModelPredictor:
    """
    Model traffic type predictor.

    It stores the best ML models in order to perform the best traffic prediction.

    :param model_base_dir: directory where the models are stored. Default to '../regression_models/'.
    :type model_base_dir: str
    :param parsed_values_file: directory where the dataset parsed values are stored.
        Default to '../output/parsed_values_dict.json'.
    :type parsed_values_file: str
    """

    def __init__(self, model_base_dir: str = MODEL_BASE_DIR,
                 parsed_values_file: str = MODEL_PARSED_VALUES_FILE) -> None:
        """
        ModelPredictor initializer.
        """

        # Initialize class variables
        self._num_models = 0
        self._performances = dict()
        self._best_models = list()

        # Retrieve models loaded directory based on the parameters
        self._base_dir = model_base_dir

        # Store the parsed values dictionary
        with open(parsed_values_file) as f:
            self._parsed_values_dict = json.load(f)

    def load_best_models(self, num_models: int = DEFAULT_NUM_MODELS, performance_file: str = MODEL_PERFORMANCE_FILE) \
            -> None:
        """
        Load the best models into the class. This number of models is specified by parameters.

        :param num_models: number of models to load. Default to 1.
        :type num_models: int
        :param performance_file: file where the training performances have been stored.
            Default to '../regression_models/ml_performance.json'.
        :type performance_file: str
        :return: None
        """
        # Store the number of models
        self._num_models = num_models

        # Load all the model performances
        with open(performance_file) as json_file:
            all_models_performances = json.load(json_file)

        # Sort models list by performance
        sorted_performances = sort_performances(all_models_performances)

        # Iterate over the models and load those that are the best
        for i in range(num_models):
            # Retrieve model name and append the correspondent suffix
            model_name = sorted_performances[i]['model']
            if model_name == 'knn':
                model_name += f'_{sorted_performances[i]["num_neighbors"]}_{sorted_performances[i]["fold"]}'
            elif model_name == 'decision_tree':
                model_name += f'_d{sorted_performances[i]["max_depth"]}_{sorted_performances[i]["fold"]}'
            elif model_name == 'random_forest':
                model_name += f'_d{sorted_performances[i]["max_depth"]}_e{sorted_performances[i]["num_estimators"]}_' \
                              f'{sorted_performances[i]["fold"]}'
            elif model_name == 'linear_regression':
                model_name += f'_{sorted_performances[i]["fold"]}'

            # Load the model into the class
            self._best_models.append(load_model(self._base_dir + model_name + '.pickle'))

    def predict(self, traffic_info: pd.DataFrame, num_models: int = DEFAULT_NUM_MODELS) -> list:
        """
        Predict the turn probabilities based on a given traffic information.

        :param traffic_info: information related to the current traffic status.
        :type traffic_info: pandas DataFrame
        :param num_models: number of models used for prediction. Default to 1.
        :type num_models: int
        :return: traffic turn predictions list or exception if invalid number of models
        :rtype: list
        """
        # Check if the number of models is valid
        if num_models <= self._num_models:
            # Create predictions list
            predictions = list()
            # Iterate over the best models
            for i in range(num_models):
                # Parse the traffic information to valid values
                traffic_info = self.parse_input_data(traffic_info)

                # KNN models uses ".values" to predict, otherwise is not required
                if isinstance(self._best_models[i], KNearestNeighbors):
                    prediction = self._best_models[i].predict(traffic_info.values)
                else:
                    prediction = self._best_models[i].predict(traffic_info)

                # Predict the traffic type and store it
                predictions.append(prediction)

            return predictions
        else:
            raise ValueError('Number of specified models is greater than the load ones, exiting...')

    def parse_input_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Parse input data for those fields that are not valid for the models such as strings.

        :param data: input dataframe which will be parsed.
        :type data: pandas DataFrame
        :return: parsed input dataframe
        :rtype: pandas DataFrame
        """
        # Iterate over parsed values
        for k, v in self._parsed_values_dict.items():
            # Retrieve current values
            for field, value in v.items():
                # Replace values
                data[k] = data[k].replace(value, field)
        return data
