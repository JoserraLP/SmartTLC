import time

import pandas as pd
import traci
from sumo_generators.static.constants import FLOWS_VALUES, TIMESTEPS_PER_HALF_HOUR
from sumo_generators.time_patterns.time_patterns import TimePattern
from sumo_generators.time_patterns.utils import retrieve_date_info
from t_predictor.generators.dataset_generator import DatasetGenerator
from t_predictor.generators.utils import get_num_passing_vehicles_detectors
from t_predictor.static.constants import TL_PROGRAMS


class TimePatternGenerator(DatasetGenerator):
    """
    Dataset generator from the TraCI simulations based on time pattern
    """

    def __init__(self, sumo_conf, time_pattern_file: str = ''):
        """
        TraCISimulator initializer.

        :param sumo_conf: SUMO configuration
        :param time_pattern_file: time pattern input file. Default is ''.
        :type time_pattern_file: str
        """

        super().__init__(sumo_conf)

        # Store the time pattern
        self._time_pattern = TimePattern(file_dir=time_pattern_file)

        # High values
        self.high_vehs_per_hour = FLOWS_VALUES['high']['vehsPerHour']
        self.high_vehs_range = FLOWS_VALUES['high']['vehs_range']
        # Medium values
        self.med_vehs_per_hour = FLOWS_VALUES['med']['vehsPerHour']
        self.med_vehs_range = FLOWS_VALUES['med']['vehs_range']
        # Low values
        self.low_vehs_per_hour = FLOWS_VALUES['low']['vehsPerHour']
        self.low_vehs_range = FLOWS_VALUES['low']['vehs_range']
        # Very Low values
        self.very_low_vehs_per_hour = FLOWS_VALUES['very_low']['vehsPerHour']
        self.very_low_vehs_range = FLOWS_VALUES['very_low']['vehs_range']

    def simulate(self) -> None:
        """
        Perform the dataset generation with time pattern by simulating with TraCI.

        :return: None
        """
        # Create start time record
        start_time = time.time()

        # Static program
        tl_program = TL_PROGRAMS[0]

        # Define initial timestep
        cur_timestep = 0

        # We first create the flows file with the loaded time pattern
        self.generate_traffic_flows_by_time_pattern(self._time_pattern.pattern)

        # SUMO is started as a subprocess and then the python script connects and runs
        traci.start([self._sumo_binary, "-c", self._config_file, "--no-warnings"])

        # Store traci instance into the class
        self._traci = traci

        # Load TL program
        for traffic_light in self._traci.trafficlight.getIDList():
            self._traci.trafficlight.setProgram(traffic_light, tl_program)

        # Retrieve traffic type
        time_pattern_id = cur_timestep / TIMESTEPS_PER_HALF_HOUR
        traffic_type = self._time_pattern.retrieve_traffic_type(time_pattern_id)

        # Initialize basic data schema
        data = {'sim_id': time_pattern_id, 'tl_id': 'c1', 'tl_program': tl_program, 'traffic_type': traffic_type,
                'passing_veh_n_s': 0, 'passing_veh_e_w': 0}

        # Initialize list with passed vehicles
        passed_vehicles = set()

        # Traci simulation
        # Iterate until there are no more vehicles
        while self._traci.simulation.getMinExpectedNumber() > 0:

            # Retrieve all the info

            # Passing veh
            passing_veh = get_num_passing_vehicles_detectors(self._traci, passed_vehicles)

            # Increase passing veh values per queue.
            data['passing_veh_n_s'] += passing_veh['n_s']
            data['passing_veh_e_w'] += passing_veh['e_w']

            # Calculate the time pattern id
            time_pattern_id = cur_timestep / TIMESTEPS_PER_HALF_HOUR

            # If next time pattern
            if time_pattern_id.is_integer() and time_pattern_id < len(self._time_pattern.pattern):
                # Retrieve date info
                date_info = retrieve_date_info(timestep=cur_timestep, time_pattern=self._time_pattern)

                # Append date info to data
                data.update(date_info)

                # Insert data
                self._storage.insert_data(data_dict=data)

                # Retrieve traffic type
                traffic_type = self._time_pattern.retrieve_traffic_type(cur_timestep / TIMESTEPS_PER_HALF_HOUR)

                # Initialize basic data schema
                data = {'sim_id': time_pattern_id, 'tl_id': 'c1', 'tl_program': tl_program,
                        'traffic_type': traffic_type, 'passing_veh_n_s': 0, 'passing_veh_e_w': 0}

            # Simulate a step
            self._traci.simulationStep()

            cur_timestep += 1

        # Close TraCI simulation in order to start another one in the next iteration
        self._traci.close()

        # Create stop time record
        stop_time = time.time()

        # Calculate elapsed time
        elapsed_time = stop_time - start_time
        print(f'Total elapsed time in simulation: {elapsed_time}')

    def generate_traffic_flows_by_time_pattern(self, time_pattern: pd.DataFrame) -> None:
        """
        Generate the traffic flows and store it on the output file.

        :param time_pattern: dataframe with the time pattern.
        :type time_pattern: pd.DataFrame
        :return: None
        """
        # Iter over the time pattern rows
        for index, row in time_pattern.iterrows():
            # Generate the row traffic flow
            self.generate_traffic_flows(traffic_type=row['traffic_type'], begin=index * TIMESTEPS_PER_HALF_HOUR,
                                        end=TIMESTEPS_PER_HALF_HOUR * (index + 1))
        # Store the flows in the output file
        self._store_flows()
