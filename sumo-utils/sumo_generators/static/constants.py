# Net constants
MIN_ROWS = 1
MIN_COLS = 1
MIN_LANES = 1
DISTANCE = 500
DET_DISTANCE = 25
DET_FREQ = 1800
JUNCTION_TYPE = "traffic_light"
TL_TYPE = "static"
TL_LAYOUT = "opposites"
DEFAULT_TIME_PATTERN_FILE = '../time_patterns/generated_calendar.csv'
ALLOW_TURNS = False

# Traffic proportions
TRAFFIC_PROPORTIONS = [0.25, 0.50, 1, 2, 4]

# Bounds on phase time
LOWER_BOUND_TIME_PHASE = 20
UPPER_BOUND_TIME_PHASE = 70
MAXIMUM_TIME_PHASE = 80
MAXIMUM_TIME_BOUND_PHASE = UPPER_BOUND_TIME_PHASE - LOWER_BOUND_TIME_PHASE

# File path constants
DEFAULT_DIR = "../config/"
# Define file names
DET_FILENAME = './out.xml'
DEFAULT_NODES_FILENAME = "topology.nod.xml"
DEFAULT_EDGES_FILENAME = "topology.edg.xml"
DEFAULT_NET_FILENAME = "topology.net.xml"
DEFAULT_DET_FILENAME = "topology.det.xml"
DEFAULT_TLL_FILENAME = "topology.tll.xml"
DEFAULT_ROUTE_FILENAME = "flows.rou.xml"
DEFAULT_CONFIG_FILENAME = "simulation.sumocfg"

# Define files paths
DET_FILE = DEFAULT_DIR + './out.xml'
DEFAULT_NODES_DIR = DEFAULT_DIR + "topology.nod.xml"
DEFAULT_EDGES_DIR = DEFAULT_DIR + "topology.edg.xml"
DEFAULT_NET_DIR = DEFAULT_DIR + "topology.net.xml"
DEFAULT_DET_DIR = DEFAULT_DIR + "topology.det.xml"
DEFAULT_TLL_DIR = DEFAULT_DIR + "topology.tll.xml"
DEFAULT_ROUTE_DIR = DEFAULT_DIR + "flows.rou.xml"
DEFAULT_CONFIG_DIR = DEFAULT_DIR + "simulation.sumocfg"

# Default date values
DEFAULT_DAY = "monday"
DEFAULT_DATE_DAY = "02"
DEFAULT_DATE_MONTH = "02"  # February
DEFAULT_DATE_YEAR = "2021"

# Date pattern fields
DATE_FIELDS = ['hour', 'day', 'date_day', 'date_month', 'date_year']

# Info schemas
EDGE_SCHEMA = '  <edge id="{id}" from="{from_node}" to="{to_node}" priority="{priority}" numLanes="{num_lanes}"/> \n'
NODE_SCHEMA = '  <node id="{id}" x="{x}" y="{y}" type="{type}" tlType="{tl_type}" tlLayout="{tl_layout}"/> \n'

# Flows generation
TIMESTEPS_PER_HALF_HOUR = 1800  # Half hour is 1800 seconds

# Flows variables and its values
FLOWS_VALUES = {
    'high': {
        'vehsPerHour': 500,
        'vehs_range': 150
    },
    'med': {
        'vehsPerHour': 150,
        'vehs_range': 45
    },
    'low': {
        'vehsPerHour': 20,
        'vehs_range': 6
    },
    'very_low': {
        'vehsPerHour': 3,
        'vehs_range': 2
    }
}

# Traffic type relation
TRAFFIC_TYPE_RELATION = {
    # (NS, EW)
    0: ('very_low', 'very_low'),
    1: ('very_low', 'low'),
    2: ('low', 'very_low'),
    3: ('low', 'low'),
    4: ('low', 'med'),
    5: ('low', 'high'),
    6: ('med', 'low'),
    7: ('med', 'med'),
    8: ('med', 'high'),
    9: ('high', 'low'),
    10: ('high', 'med'),
    11: ('high', 'high'),
}


# Number of traffic types
NUM_TRAFFIC_TYPES = len(TRAFFIC_TYPE_RELATION)

# Available traffic types
TRAFFIC_TYPES = {
    'very_low': 0,
    'low': 1,
    'med': 2,
    'high': 3
}


# Grid network 1x1 parser
GRID_1x1_DICT = {
    'c1_c0': [('n1', 'right', 'c1_w1'), ('s1', 'left', 'c1_w1'), ('s1', 'forward', 'c1_n1'), ('e1', 'forward', 'c1_w1')],
    'c1_c2': [('n1', 'forward', 'c1_s1'), ('w1', 'right', 'c1_s1'), ('w1', 'forward', 'c1_e1'), ('e1', 'left', 'c1_s1')],
}

# MQTT constants
MQTT_URL = '172.20.0.2'
MQTT_PORT = 1883
TRAFFIC_INFO_TOPIC = 'traffic_info'
TRAFFIC_PREDICTION_TOPIC = 'traffic_prediction'
TURN_PREDICTION_TOPIC = 'turn_prediction'
TRAFFIC_ANALYSIS_TOPIC = 'traffic_analysis'
DEFAULT_QOS = 0

# Topology database constants
DB_IP_ADDRESS = '172.20.0.9:7687'
DB_USER = 'neo4j'
DB_PASSWORD = 'admin'

# Eclipse SUMO default configuration file
DEFAULT_CONFIG_FILE = '../config/simulation.sumocfg'

# Default detector file
DEFAULT_DETECTOR_FILE = 'detectors.add.xml'
DEFAULT_DETECTOR_POS = 10.0
DEFAULT_DETECTOR_FREQ = 1800

# Monitoring temporal window in minutes
DEFAULT_TEMPORAL_WINDOW = 5

# Simulation steps monitoring temporal windows in seconds
TIMESTEPS_TO_STORE_INFO = 300  # 5 Cycles = 300 seconds

# Default turn dictionary
DEFAULT_TURN_DICT = {'turn_prob_right': 0.20, 'turn_prob_left': 0.20, 'turn_prob_forward': 0.60}