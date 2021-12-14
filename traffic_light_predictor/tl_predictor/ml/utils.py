from sklearn.metrics import accuracy_score, precision_recall_fscore_support

import pickle
import os


def check_file_extension(file_dir):
    # Retrieve filename and extension
    filename, filename_ext = os.path.splitext(file_dir)
    # Parse to a .pickle extension
    if filename_ext == '' or filename_ext != '.pickle':
        filename_ext = '.pickle'

    # Create the new file extension
    return filename + filename_ext


def save_model(model: object, output_dir: str):
    # Check file extension
    output_dir = check_file_extension(output_dir)

    # Open file to dump the model
    f = open(output_dir, 'wb')
    # Dump the model
    pickle.dump(model, f)
    # Close the output file
    f.close()


def load_model(input_dir: str):
    # Check input classifier file
    input_dir = check_file_extension(input_dir)
    # Read from input file
    f = open(input_dir, 'rb')
    # Retrieve model
    model = pickle.load(f)
    # Close file
    f.close()
    return model


def calculate_results(test_target_dataset, pred_target_dataset):
    # Retrieve accuracy
    accuracy = accuracy_score(test_target_dataset, pred_target_dataset)
    # Retrieve precision, recall and F1 score
    precision, recall, f1_score, _ = precision_recall_fscore_support(test_target_dataset, pred_target_dataset,
                                                                     zero_division=0)
    # Zero division = 0 because there are classes that are not represented in the dataset

    return accuracy, precision, recall, f1_score
