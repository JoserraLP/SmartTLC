import time
import pandas as pd

from tl_predictor.ml.utils import calculate_pred_metrics


class BaseClassification:
    """
    Base Classification algorithm class
    """

    def __init__(self):
        """
        Base Classification initializer
        """
        self._model = None

    def train(self, train_features_dataset: pd.DataFrame, train_target_dataset: pd.DataFrame):
        """
        Train the model

        :param train_features_dataset: Train features dataset
        :type train_features_dataset: pd.DataFrame
        :param train_target_dataset: Train target dataset
        :type train_target_dataset: pd.DataFrame
        """
        self._model.fit(train_features_dataset, train_target_dataset.values.ravel())

    def predict(self, features_dataset: pd.DataFrame):
        """
        Predict the value from the features dataset

        :param features_dataset: Input features dataset
        :type features_dataset: pd.DataFrame
        :return: model prediction
        :rtype: pd.DataFrame
        """
        return self._model.predict(features_dataset)

    def training_process(self, train_features_dataset: pd.DataFrame, train_target_dataset: pd.DataFrame,
                         test_features_dataset: pd.DataFrame, test_target_dataset: pd.DataFrame):
        """
        Start the training process of the model and store its performance values.

        :param train_features_dataset: Train features dataset
        :type train_features_dataset: pd.DataFrame
        :param train_target_dataset: Train target dataset
        :type train_target_dataset: pd.DataFrame
        :param test_features_dataset: Test features dataset
        :type test_features_dataset: pd.DataFrame
        :param test_target_dataset: Test target dataset
        :type test_target_dataset: pd.DataFrame
        :return: model performance metrics as elapsed time, accuracy, precision, recall and f1 score
        """
        # Get start time
        t0 = time.time()

        # Perform training process
        self.train(train_features_dataset, train_target_dataset)

        # Perform the test dataset prediction
        pred_target_dataset = self.predict(test_features_dataset)

        # Get end time
        t1 = time.time()

        # Calculate elapsed time
        elapsed_time = t1 - t0

        # Calculate the results
        accuracy, precision, recall, f1_score = calculate_pred_metrics(test_target_dataset, pred_target_dataset)

        return elapsed_time, accuracy, precision, recall, f1_score
