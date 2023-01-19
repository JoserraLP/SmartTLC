# Options default values
DEFAULT_OUTPUT_FILE = '../../sumo-utils/time_patterns/calendar_time_pattern.csv'

# Time patterns default folder
DEFAULT_BASE_TIME_PATTERNS_FOLDER = '../../sumo-utils/time_patterns/base_patterns/'

# Default calendar csv file
DEFAULT_CALENDAR_FILE = '../../sumo-utils/time_patterns/calendar.csv'

# Default output generated calendar csv file
DEFAULT_GENERATED_CALENDAR_FILE = '../../sumo-utils/time_patterns/generated_calendar.csv'

# Number of rows per day
NUM_ROWS_PER_DAY = 24

# Random ranges for noise generation on calendar
# Variance for traffic type
RANDOM_TRAFFIC_TYPE_LOWER_BOUND = -1
RANDOM_TRAFFIC_TYPE_UPPER_BOUND = 1
RANDOM_TRAFFIC_TYPE_RANGE = NUM_ROWS_PER_DAY * 3  # 24 rows per 3 days
# Variance of swapping from working to weekend days or bank-holidays
RANDOM_WORKING_TO_OTHER_SWAP_RANGE = 50  # 50 days
# Variance of swapping from weekend to working
RANDOM_WEEKEND_TO_WORKING_SWAP_RANGE = 20  # 20 days

# ML constants
KNN_MAX_NEIGHBORS = 15
DT_MAX_DEPTH = 20
RF_NUM_ESTIMATORS = 20
RF_MAX_DEPTH = 10
MODEL_BASE_DIR = '../classifier_models/'
MODEL_PERFORMANCE_FILE = '../classifier_models/ml_performance.json'
MODEL_PARSED_VALUES_FILE = '../output/parsed_values_dict.json'
DEFAULT_NUM_MODELS = 1
MODEL_NUM_FOLDS = 2

# Prediction columns schema
COLUMNS_PREDICTOR = ['hour', 'day', 'date_day', 'date_month', 'date_year']
