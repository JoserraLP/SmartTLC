import argparse
import json
import os
import shutil

import numpy as np
import pandas as pd
from turns_predictor.ml.dataset import TurnDataset
from turns_predictor.ml.model_predictor import ModelPredictor
from turns_predictor.ml.model_trainer import ModelTrainer
from turns_predictor.providers.predictor import TurnPredictor
from turns_predictor.static.argparse_types import check_file, check_dimension, check_valid_prediction_info, \
    check_greater_zero
from turns_predictor.static.constants import MODEL_BASE_DIR, MODEL_PARSED_VALUES_FILE, \
    MODEL_PERFORMANCE_FILE, DEFAULT_NUM_MODELS, MODEL_NUM_FOLDS

from sumo_generators.static.constants import MQTT_URL, MQTT_PORT


def get_options():
    """
    Define options for the execution command.

    :return: Argument options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Predictors of turning probabilities based on a given road.')

    # Define generator groups

    # Train group
    train_group = arg_parser.add_argument_group("Training options", description="Parameters related to the training "
                                                                                "process of the ML models")
    train_group.add_argument("-t", "--train", dest="input_file", type=check_file, action="store",
                             help="input turn pattern file")
    train_group.add_argument("--rows", dest="rows", type=check_dimension, action="store",
                             help="rows topology")
    train_group.add_argument("--cols", dest="cols", type=check_dimension, action="store",
                             help="cols topology")
    train_group.add_argument("-f" "--folds", dest="folds", type=check_greater_zero, default=MODEL_NUM_FOLDS,
                             action="store",
                             help=f"k-fold number of folds. Default is {MODEL_NUM_FOLDS}")
    train_group.add_argument("-c", "--clean", dest="clean", action="store_true",
                             default=False, help="clean the model files.")

    # Predict value group
    predict_group = arg_parser.add_argument_group("Prediction Options", description="Parameters related to the "
                                                                                    "prediction process")
    predict_group.add_argument("-p", "--predict", dest="predict", action="store", type=check_valid_prediction_info,
                               help="predict the given value: road,hour,date_day,date_month,date_year.")

    # Full component group
    component_group = arg_parser.add_argument_group("Component Options", "Parameters related to the Docker component")
    component_group.add_argument("--component", dest="component", action="store_true", default=True,
                                 help="deploy the full component")
    component_group.add_argument("-n", "--num-models", dest="num_models", action="store", type=check_greater_zero,
                                 help=f"number of models used for the predictor. Default is {DEFAULT_NUM_MODELS}",
                                 default=DEFAULT_NUM_MODELS)
    component_group.add_argument("--middleware_host", dest="mqtt_url", action="store", type=str,
                                 help=f"middleware broker host. Default is {MQTT_URL}", default=MQTT_URL)
    component_group.add_argument("--middleware_port", dest="mqtt_port", action="store", type=int,
                                 help=f"middleware broker port. Default is {MQTT_PORT}", default=MQTT_PORT)

    args = arg_parser.parse_args()
    return args


if __name__ == "__main__":

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Training process
    if exec_options.input_file:
        # Define the input dataset file
        dataset = TurnDataset(file_dir=exec_options.input_file, cols=int(exec_options.cols),
                              rows=int(exec_options.rows))

        # Remove the model weights files
        if exec_options.clean:
            # If the directory is not empty clean it
            if len(os.listdir(MODEL_BASE_DIR)) != 0:
                for filename in os.listdir(MODEL_BASE_DIR):
                    file_path = os.path.join(MODEL_BASE_DIR, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))

        # Create model trainer
        model = ModelTrainer(dataset=dataset)

        # Perform the training process of all the models with a k-fold process
        performances = model.train(k=exec_options.folds)

        # Store the results
        with open(MODEL_PERFORMANCE_FILE, 'w', encoding='utf-8') as f:
            json.dump(performances, f, ensure_ascii=False, indent=4)

    elif exec_options.predict:  # Prediction process
        # Parse data and store it as a DataFrame
        data = exec_options.predict.replace(' ', '').split(',')
        # Create dataframe with the input data
        data = pd.DataFrame(np.array([data]), columns=['road', 'hour', 'date_day', 'date_month', 'date_year'])

        # Create model predictor
        model = ModelPredictor()

        # Load best models (only the best one as it is for testing purpose)
        model.load_best_models(num_models=1)

        # Parse data invalid values
        with open(MODEL_PARSED_VALUES_FILE) as f:
            parsed_values_dict = json.load(f)
        for k, v in parsed_values_dict.items():
            for field, value in v.items():
                data[k] = data[k].replace(value, field)

        # Show prediction
        print(model.predict(data, num_models=1))
    elif exec_options.component:  # Component process
        # Start predictor process
        predictor = TurnPredictor(mqtt_url=exec_options.mqtt_url, mqtt_port=exec_options.mqtt_port,
                                  num_models=exec_options.num_models)
