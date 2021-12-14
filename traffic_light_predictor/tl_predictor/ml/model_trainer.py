import json
import os

from tl_predictor.ml.classification_algorithms import KNearestNeighbors, NaiveBayes, SVM, RandomForest, DecisionTree
from tl_predictor.ml.dataset import SimulationDataset
from tl_predictor.ml.utils import save_model
from tl_predictor.static.constants import MODEL_BASE_DIR_CONTEXT, MODEL_BASE_DIR_DATE, MODEL_PARSED_VALUES_FILE, \
    MODEL_PERFORMANCE_FILE_DATE, MODEL_PERFORMANCE_FILE_CONTEXT, DEFAULT_OUTPUT_FILE, KNN_MAX_NEIGHBORS, DT_MAX_DEPTH, \
    RF_NUM_ESTIMATORS, RF_MAX_DEPTH, MODEL_NUM_FOLDS


class ModelTrainer:
    """
    Class for training all the different Machine Learning models.
    """

    def __init__(self, dataset_dir: str = DEFAULT_OUTPUT_FILE, model_base_dir: str = '',
                 parsed_values_file: str = MODEL_PARSED_VALUES_FILE, performance_file: str = '', date: bool = True) \
            -> None:
        """
        ModelTrainer initializer.
        
        :param dataset_dir: Directory where the input dataset is stored. Default to ../output/simulation_calendar.csv.
        :type dataset_dir: str
        :param model_base_dir: directory where the models are stored. Default to ''. If empty, use default values with
            'date' flag.
        :type model_base_dir: str
        :param parsed_values_file: directory where the dataset parsed values are stored. 
            Default to ../output/parsed_values_dict.json.
        :type parsed_values_file: str
        :param performance_file: File where the training performances have been stored. Default to ''.
            If empty, use default values with 'date' flag.
        :type performance_file: str
        :param date: if True train models based on date only, otherwise with contextual information too.
            Default to True.
        :type date: bool
        """
        # Initialize class variables
        self._performances = list()
        self._models = list()
        self._date = date
        self._parsed_values_file = parsed_values_file

        # Retrieve models loaded dir base on the parameters
        if model_base_dir != '':
            self._base_dir = model_base_dir
        else:
            if date:
                self._base_dir = MODEL_BASE_DIR_DATE
            else:
                self._base_dir = MODEL_BASE_DIR_CONTEXT

        # If the directory does not exists, create it
        if not os.path.exists(self._base_dir):
            os.makedirs(self._base_dir)

        # Retrieve models performance dir base on the parameters
        if performance_file != '':
            self._performance_file = performance_file
        else:
            if date:
                self._performance_file = MODEL_PERFORMANCE_FILE_DATE
            else:
                self._performance_file = MODEL_PERFORMANCE_FILE_CONTEXT

        # Define the input dataset file
        self._dataset = SimulationDataset(file_dir=dataset_dir, date=date)

        # Clean up the dataset
        parsed_values = self._dataset.clean_up_dataset()

        # Store the parsed values into a file
        with open(parsed_values_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_values, f, ensure_ascii=False, indent=4)

    def train(self, k: int = MODEL_NUM_FOLDS) -> list:
        """
        Perform training process of all the ML models. It can be both simple training, test split or k-fold split.

        :param k: number of folds for using the k-fold process. Default to 2.
        :type k: int
        :return: performances of the training process.
        :rtype: list
        """

        # Retrieve k-fold datasets
        k_fold_datasets = self._dataset.k_fold_split(k=k)

        # Iterate over the folds
        for index, k_fold_dataset in enumerate(k_fold_datasets):

            # Naive Bayes
            self.train_model(model_name='naive_bayes', k_fold_dataset=k_fold_dataset, k_fold_index=index)

            # SVM Linear
            self.train_model(model_name='svm_linear', k_fold_dataset=k_fold_dataset, k_fold_index=index)

            # SVM Polynomial
            self.train_model(model_name='svm_polynomial_2', k_fold_dataset=k_fold_dataset, k_fold_index=index)

            # KNN
            for num_neighbors in range(1, KNN_MAX_NEIGHBORS):
                self.train_model(model_name="knn", k_fold_dataset=k_fold_dataset, k_fold_index=index,
                                 num_neighbors=num_neighbors)

            # Decision Tree
            for max_depth in range(2, DT_MAX_DEPTH, 2):
                self.train_model(model_name="decision_tree", k_fold_dataset=k_fold_dataset, k_fold_index=index,
                                 max_depth=max_depth)

            # Random Forest
            # Iterate over the estimators
            for num_estimators in range(1, RF_NUM_ESTIMATORS):
                # Iterate over the depth
                for max_depth in range(2, RF_MAX_DEPTH, 2):
                    self.train_model('random_forest', k_fold_dataset=k_fold_dataset, k_fold_index=index,
                                     max_depth=max_depth, num_estimators=num_estimators)
        return self._performances

    def train_model(self, model_name: str, k_fold_dataset: dict, k_fold_index: int, num_neighbors: int = -1,
                    max_depth: int = -1, num_estimators: int = -1) -> None:
        """
        Train a model specified by parameter and store its performance.

        :param model_name: model name
        :type model_name: str
        :param k_fold_dataset: dict with all the fold datasets (X_train, y_train, X_test, y_test)
        :type k_fold_dataset: dict
        :param k_fold_index: fold index
        :type k_fold_index: int
        :param num_neighbors: number of neighbors for the KNN algorithm. Default to -1, that means not used.
        :type num_neighbors: int
        :param max_depth: maximum depth of the decision tree or estimator. Default to -1, that means not used.
        :type max_depth: int
        :param num_estimators: number of estimators used in the random forest. Default to -1, that means not used.
        :type num_estimators: int
        :return: None
        """
        # Define model and its directory
        if model_name == 'naive_bayes':
            model = NaiveBayes()
            model_dir = self._base_dir + f'{model_name}_{k_fold_index}.pickle'
        elif model_name == 'svm_linear':
            model = SVM(kernel='linear')
            model_dir = self._base_dir + f'{model_name}_{k_fold_index}.pickle'
        elif model_name == 'svm_polynomial_2':
            model = SVM(kernel='rbf', degree=2)
            model_dir = self._base_dir + f'{model_name}_{k_fold_index}.pickle'
        elif model_name == 'knn' and num_neighbors != -1:
            model = KNearestNeighbors(num_neighbors=num_neighbors)
            model_dir = self._base_dir + f'knn_{num_neighbors}_{k_fold_index}.pickle'
        elif model_name == 'decision_tree' and max_depth != -1:
            model = DecisionTree(max_depth=max_depth)
            model_dir = self._base_dir + f'decision_tree_d{max_depth}_{k_fold_index}.pickle'
        elif model_name == 'random_forest' and max_depth != -1 and num_estimators != -1:
            model = RandomForest(num_estimators=num_estimators, max_depth=max_depth)
            model_dir = self._base_dir + f'random_forest_d{max_depth}_e{num_estimators}_{k_fold_index}.pickle'
        else:  # Non-valid name
            model = None
            model_dir = ''

        # If the model does not exists, train it
        if model_dir != '' and not os.path.exists(model_dir):
            # Perform training_process
            # KNN is special as it uses the values field for the X datasets
            if model_name == 'knn':
                elapsed_time, accuracy, precision, recall, f1_score = model.training_process(
                    k_fold_dataset['X_train'].values,
                    k_fold_dataset['y_train'],
                    k_fold_dataset['X_test'].values,
                    k_fold_dataset['y_test'])

            else:
                elapsed_time, accuracy, precision, recall, f1_score = model.training_process(
                    k_fold_dataset['X_train'],
                    k_fold_dataset['y_train'],
                    k_fold_dataset['X_test'],
                    k_fold_dataset['y_test'])

            # Retrieve results
            results = {'elapse_time': elapsed_time, 'accuracy': accuracy,
                       'precision': precision.mean(), 'recall': recall.mean(),
                       'f1_score': f1_score.mean(), 'fold': k_fold_index, 'model': model_name}

            # Append additional information
            if model_name == 'knn':
                results['num_neighbors'] = num_neighbors
            elif model_name == 'decision_tree':
                results['max_depth'] = max_depth
            elif model_name == 'random_forest':
                results['max_depth'] = max_depth
                results['num_estimators'] = num_estimators

            # Append results
            self._performances.append(results)

            # Save the model
            save_model(model, model_dir)
