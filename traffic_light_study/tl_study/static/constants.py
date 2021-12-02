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

# Output directory where the flows will be stored
FLOWS_OUTPUT_DIR = '../net-files/flows/flows.rou.xml'

# All the possible TL programs
# TL_PROGRAMS = ['static_program', 'actuated_program', 'actuated_program_time_gap', 'actuated_program_time_loss']
TL_PROGRAMS = [f'static_program_{i}' for i in range(1, 14)]


# Timestep range for storing info into the dataset
TIMESTEPS_TO_STORE_INFO = 1800  # Equal to 30 minutes

# Number of traffic types
NUM_TRAFFIC_TYPES = 11

# Options default values
DEFAULT_GUI_FLAG = False
DEFAULT_NUMBER_OF_SIMULATIONS = 0
DEFAULT_CLI_VISUALIZE_FLAG = False
DEFAULT_CONFIG_FILE = '../net-files/config/simulation.sumocfg'
DEFAULT_OUTPUT_FILE = '../output/simulation.csv'
