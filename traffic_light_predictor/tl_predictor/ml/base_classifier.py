import time

from tl_predictor.ml.utils import calculate_results


class BaseClassification:

    def __init__(self):
        self._model = None

    def train(self, train_features_dataset, train_target_dataset):
        self._model.fit(train_features_dataset, train_target_dataset.values.ravel())

    def predict(self, features_dataset):
        return self._model.predict(features_dataset)

    def training_process(self, train_features_dataset, train_target_dataset, test_features_dataset,
                         test_target_dataset):
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
        accuracy, precision, recall, f1_score = calculate_results(test_target_dataset, pred_target_dataset)

        return elapsed_time, accuracy, precision, recall, f1_score

    def plot(self):
        # TODO
        pass
