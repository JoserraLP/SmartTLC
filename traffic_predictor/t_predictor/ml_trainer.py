import json
import optparse
import os
import shutil

import pandas as pd
from t_predictor.ml.dataset import SimulationDataset
from t_predictor.ml.model_predictor import ModelPredictor
from t_predictor.ml.model_trainer import ModelTrainer
from t_predictor.providers.predictor import Predictor
from t_predictor.static.constants import MODEL_BASE_DIR_DATE, MODEL_BASE_DIR_CONTEXT, \
    MODEL_PARSED_VALUES_FILE, MQTT_URL, MQTT_PORT, MODEL_PERFORMANCE_FILE_DATE, MODEL_PERFORMANCE_FILE_CONTEXT


def get_options():
    """
    Define options for the executable script.

    :return: options
    :rtype: object
    """
    optParser = optparse.OptionParser()

    # General option
    optParser.add_option("-d", "--date", dest="date", action="store_true", default=False,
                         help="Train models based on date. "
                              "If not specified, train models based on context and date (default).")

    # Input dataset group
    train_group = optparse.OptionGroup(optParser, "Training Options", "Training tools")
    train_group.add_option("-t", "--train", dest="input_file", metavar='FILE', action="store",
                           help="input file")
    train_group.add_option("-c", "--clean", dest="clean", action="store_true",
                           default=False, help="clean the model files.")
    optParser.add_option_group(train_group)

    # Predict value group
    predict_group = optparse.OptionGroup(optParser, "Prediction Options", "Prediction tools")
    predict_group.add_option("-p", "--predict", dest="predict", action="store",
                             help="predict the given value: passing_veh_e_w, passing_veh_n_s, hour, day, date_day, "
                                  "date_month, date_year. If 'date' flag active, the fields are: hour, day, date_day, "
                                  "date_month, date_year")
    optParser.add_option_group(predict_group)

    # Full component group
    component_group = optparse.OptionGroup(optParser, "Component Options", "Component tools")
    component_group.add_option("--component", dest="component", action="store_true", default=True,
                               help="deploy the full component")
    component_group.add_option("-n", "--num-models", dest="num_models", action="store",
                               help="number of models used for the predictor")
    component_group.add_option("--middleware_host", dest="mqtt_url", action="store",
                               help="middleware broker host")
    component_group.add_option("--middleware_port", dest="mqtt_port", action="store",
                               help="middleware broker port")
    optParser.add_option_group(component_group)

    options, args = optParser.parse_args()
    return options


if __name__ == "__main__":

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Training process
    if exec_options.input_file:
        # Define the input dataset file
        dataset = SimulationDataset(file_dir=exec_options.input_file)

        # Clean up the dataset
        parsed_values = dataset.clean_up_dataset()

        # Store the parsed values into a file
        with open(MODEL_PARSED_VALUES_FILE, 'w', encoding='utf-8') as f:
            json.dump(parsed_values, f, ensure_ascii=False, indent=4)

        # Remove the model files
        if exec_options.clean:
            # Get kind of predictor selected
            if exec_options.date:
                model_base_dir = MODEL_BASE_DIR_DATE
            else:
                model_base_dir = MODEL_BASE_DIR_CONTEXT

            # If the directory is not empty clean it
            if len(os.listdir(model_base_dir)) != 0:
                for filename in os.listdir(model_base_dir):
                    file_path = os.path.join(model_base_dir, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))

        # Create model trainer
        model = ModelTrainer(dataset_dir=exec_options.input_file, date=exec_options.date)

        # Perform the training process of all the models with a k-fold process
        performances = model.train(k=2)

        # Set performance file
        if exec_options.date:
            performance_file = MODEL_PERFORMANCE_FILE_DATE
        else:
            performance_file = MODEL_PERFORMANCE_FILE_CONTEXT

        # Store the results
        with open(performance_file, 'w', encoding='utf-8') as f:
            json.dump(performances, f, ensure_ascii=False, indent=4)

    else:
        # Prediction process
        if exec_options.predict:
            # Parse data and store it as a DataFrame
            data = exec_options.predict.replace(' ', '').split(',')
            if exec_options.date:
                data = pd.DataFrame(np.array([data]),
                                    columns=['hour', 'day', 'date_day', 'date_month', 'date_year'])
            else:
                data = pd.DataFrame(np.array([data]),
                                    columns=['passing_veh_e_w', 'passing_veh_n_s', 'hour', 'day', 'date_day',
                                             'date_month', 'date_year'])
            # Create model predictor
            model = ModelPredictor(exec_options.date)
            # Load best models
            model.load_best_models(num_models=1)

            # Parse data invalid values
            with open(MODEL_PARSED_VALUES_FILE) as f:
                parsed_values_dict = json.load(f)
            for k, v in parsed_values_dict.items():
                for field, value in v.items():
                    data[k] = data[k].replace(value, field)

            # Show prediction
            print(model.predict(data, num_models=1))
        else:
            # Component process
            if exec_options.component:
                # Retrieve parameter values or default values
                if exec_options.num_models:
                    num_models = int(exec_options.num_models)
                else:
                    num_models = 1

                if exec_options.mqtt_url:
                    mqtt_url = exec_options.mqtt_url
                else:
                    mqtt_url = MQTT_URL

                if exec_options.mqtt_port:
                    mqtt_port = int(exec_options.mqtt_port)
                else:
                    mqtt_port = MQTT_PORT

                # Start predictor process
                predictor = Predictor(date=exec_options.date, mqtt_url=mqtt_url, mqtt_port=mqtt_port,
                                      num_models=num_models)
