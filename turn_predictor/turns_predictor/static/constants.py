# ML constants
KNN_MAX_NEIGHBORS = 15
DT_MAX_DEPTH = 20
RF_NUM_ESTIMATORS = 20
RF_MAX_DEPTH = 10
MODEL_BASE_DIR = '../regression_models/'
MODEL_PERFORMANCE_FILE = '../regression_models/ml_performance.json'
MODEL_PARSED_VALUES_FILE = '../output/parsed_values_dict.json'
DEFAULT_NUM_MODELS = 1
MODEL_NUM_FOLDS = 2

# MQTT constants
MQTT_URL = '172.20.0.2'
MQTT_PORT = 1883
TRAFFIC_INFO_TOPIC = 'traffic_info'
PREDICTION_TOPIC = 'turn_prediction'

DEFAULT_TURN_DICT = {'turn_prob_right': 0.20, 'turn_prob_left': 0.20, 'turn_prob_forward': 0.60}
