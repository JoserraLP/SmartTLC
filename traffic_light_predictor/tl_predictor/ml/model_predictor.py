import json

import pandas as pd
from tl_predictor.ml.classification_algorithms import KNearestNeighbors
from tl_predictor.ml.utils import load_model
from tl_predictor.static.constants import MODEL_BASE_DIR_DATE, MODEL_BASE_DIR_CONTEXT, MODEL_PERFORMANCE_FILE_CONTEXT, \
    MODEL_PERFORMANCE_FILE_DATE, MODEL_PARSED_VALUES_FILE, DEFAULT_NUM_MODELS


def sort_performances(performances: list) -> list:
    """
    Sort the performances list by the 'f1_score' field.

    :param performances: list with model's performances.
    :type performances: list
    :return: sorted list
    :rtype: list
    """
    return sorted(performances, key=lambda x: x['f1_score'], reverse=True)


class ModelPredictor:
    """
    Model traffic type predictor.

    It stores the best ML models in order to perform the best traffic prediction.
    """

    def __init__(self, date: bool = True, model_base_dir: str = '', parsed_values_file: str = MODEL_PARSED_VALUES_FILE) \
            -> None:
        """
        ModelPredictor initializer.

        :param date: if True train models based on date only, otherwise with contextual information too.
            Default to True.
        :type date: bool
        :param model_base_dir: directory where the models are stored. Default to ''. If empty, use default values with
            'date' flag.
        :type model_base_dir: str
        :param parsed_values_file: directory where the dataset parsed values are stored.
            Default to '../output/parsed_values_dict.json'.
        :type parsed_values_file: str
        """

        # Initialize class variables
        self._num_models = 0
        self._performances = dict()
        self._best_models = list()
        self._date = date

        # Retrieve models loaded dir base on the parameters
        if model_base_dir != '':
            self._base_dir = model_base_dir
        else:
            if date:
                self._base_dir = MODEL_BASE_DIR_DATE
            else:
                self._base_dir = MODEL_BASE_DIR_CONTEXT

        # Store the parsed values dictionary
        with open(parsed_values_file) as f:
            self._parsed_values_dict = json.load(f)

    def load_best_models(self, num_models: int = DEFAULT_NUM_MODELS, performance_file: str = '') \
            -> None:
        """
        Load the best models into the class. This number of models is specified by parameters.

        :param num_models: Number of models to load. Default to 1.
        :type num_models: int
        :param performance_file: File where the training performances have been stored. Default to ''.
            If empty, use default values with 'date' flag.
        :type performance_file: str
        :return: None
        """
        # Store the number of models
        self._num_models = num_models

        # Retrieve models performance dir base on the parameters
        if performance_file != '':
            performance_file = performance_file
        else:
            if self._date:
                performance_file = MODEL_PERFORMANCE_FILE_DATE
            else:
                performance_file = MODEL_PERFORMANCE_FILE_CONTEXT

        # Load all the model performances and sort them
        with open(performance_file) as json_file:
            all_models = json.load(json_file)
        sorted_performances = sort_performances(all_models)

        # Iterate over the models and load those that are the best
        for i in range(num_models):
            # Retrieve model name and append the correspondent suffix
            model_name = sorted_performances[i]['model']
            if model_name == 'knn':
                model_name += f'_{sorted_performances[i]["num_neighbors"]}_{sorted_performances[i]["fold"]}'
            if model_name == 'decision_tree':
                model_name += f'_d{sorted_performances[i]["max_depth"]}_{sorted_performances[i]["fold"]}'
            if model_name == 'random_forest':
                model_name += f'_d{sorted_performances[i]["max_depth"]}_e{sorted_performances[i]["num_estimators"]}_' \
                              f'{sorted_performances[i]["fold"]}'
            if model_name in ['naive_bayes', 'svm_linear', 'smv_polynomial_2']:
                model_name += f'_{sorted_performances[i]["fold"]}'

            # Load the model into the class
            self._best_models.append(load_model(self._base_dir + model_name + '.pickle'))

    def predict(self, traffic_info: pd.DataFrame, num_models: int = DEFAULT_NUM_MODELS) -> list:
        """
        Predict the traffic type of a given traffic information.

        :param traffic_info: information related to the current traffic status.
        :type traffic_info: pandas DataFrame
        :param num_models: number of models used for prediction. Default to 1.
        :type num_models: int
        :return: traffic type predictions list or exception if invalid number of models
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

                if isinstance(self._best_models[i], KNearestNeighbors):
                    prediction = self._best_models[i].predict(traffic_info.values)[0]
                else:
                    prediction = self._best_models[i].predict(traffic_info)[0]

                # Predict the traffic type and store it
                predictions.append(prediction)

            return predictions
        else:
            raise ValueError('Number of specified models is greater than the load ones, exiting...')

    def parse_input_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Parse input data for those fields that are not valid for the models such as strings.

        :param data: input dataframe which will be modified.
        :type data: pandas DataFrame
        :return: parsed dataframe
        :rtype: pandas DataFrame
        """
        # Iterate over parsed values
        for k, v in self._parsed_values_dict.items():
            # Retrieve current values
            for field, value in v.items():
                # Replace values
                data[k] = data[k].replace(value, field)
        return data
