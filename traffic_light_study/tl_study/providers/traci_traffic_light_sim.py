import traci

from tl_study.providers.traci_sim import TraCISimulator
from tl_study.providers.utils import get_total_waiting_time_per_lane, get_num_passing_vehicles_detectors
from tl_study.static.constants import NUM_TRAFFIC_TYPES, TL_PROGRAMS, MAXIMUM_TIME_BOUND_PHASE


class TrafficTypeSimulator(TraCISimulator):
    """
    Dataset generator from the TraCI simulations
    """

    def __init__(self, sumo_conf, tl_interval: int = -1):
        """
        TraCISimulator initializer.

        :param sumo_conf: SUMO configuration
        :param tl_interval: traffic light phase time intervals.
            Default to -1 that means use the default proportion tl algorithm
        :type tl_interval: int
        """

        # SUMO configuration files
        super().__init__(sumo_conf)
        # Store the TL interval
        self._tl_interval = tl_interval

    def simulate(self):
        """
        Perform the dataset generation with number of simulations by simulating with TraCI.

        :return: None
        """
        if self._tl_interval != -1:
            # Generate static program names by traffic light interval
            tl_programs = [f'static_program_{i+1}' for i in
                           range(0, int(MAXIMUM_TIME_BOUND_PHASE / self._tl_interval) + 1)]
        else:
            tl_programs = TL_PROGRAMS

        # Loop for all the simulations
        for sim_id in range(0, (NUM_TRAFFIC_TYPES+1) * len(tl_programs)):
            # Retrieve simulation TL program
            tl_program = tl_programs[int(sim_id / (NUM_TRAFFIC_TYPES + 1))]
            # Retrieve simulation traffic type
            traffic_type = sim_id % (NUM_TRAFFIC_TYPES + 1)

            # Initialize basic data schema
            data = {'sim_id': sim_id, 'tl_id': 'c1', 'tl_program': tl_program, 'traffic_type': traffic_type,
                    'waiting_time_veh_n_s': 0, 'waiting_time_veh_e_w': 0, 'num_passing_veh_n_s': 0,
                    'num_passing_veh_e_w': 0}

            # We first create the flows file, by doing this, sumo will always have a flows file
            self.generate_traffic_flows(traffic_type)
            # Store the flows
            self._store_flows()

            # SUMO is started as a subprocess and then the python script connects and runs
            traci.start([self._sumo_binary, "-c", self._config_file, "--no-warnings"])

            # Store traci instance into the class
            self._traci = traci

            # Load TL program
            for traffic_light in self._traci.trafficlight.getIDList():
                self._traci.trafficlight.setProgram(traffic_light, tl_program)

            # Initialize the dict
            total_waiting_time = {'c1': {'n': 0, 's': 0, 'e': 0, 'w': 0}}
            prev_total_waiting_time_per_lane = get_total_waiting_time_per_lane(traci)

            # Initialize the set
            vehicles_passed = set()

            # Traci simulation
            # Iterate until there are no more vehicles
            while self._traci.simulation.getMinExpectedNumber() > 0:
                # Retrieve all the info

                # Waiting time
                current_total_waiting_time = get_total_waiting_time_per_lane(traci)
                # Iterate over the current time on lanes
                for junction, lanes in current_total_waiting_time.items():
                    for lane, waiting_time in lanes.items():
                        # Store when the waiting time is calculated
                        if prev_total_waiting_time_per_lane[junction][lane] > waiting_time:
                            # Store by direction
                            if 'n' in lane:
                                if total_waiting_time[junction]['n'] == 0:
                                    total_waiting_time[junction]['n'] = prev_total_waiting_time_per_lane[junction][lane]
                                else:
                                    total_waiting_time[junction]['n'] += prev_total_waiting_time_per_lane[junction][
                                        lane]
                            if 's' in lane:
                                if total_waiting_time[junction]['s'] == 0:
                                    total_waiting_time[junction]['s'] = prev_total_waiting_time_per_lane[junction][lane]
                                else:
                                    total_waiting_time[junction]['s'] += prev_total_waiting_time_per_lane[junction][
                                        lane]
                            if 'e' in lane:
                                if total_waiting_time[junction]['e'] == 0:
                                    total_waiting_time[junction]['e'] = prev_total_waiting_time_per_lane[junction][lane]
                                else:
                                    total_waiting_time[junction]['e'] += prev_total_waiting_time_per_lane[junction][
                                        lane]
                            if 'w' in lane:
                                if total_waiting_time[junction]['w'] == 0:
                                    total_waiting_time[junction]['w'] = prev_total_waiting_time_per_lane[junction][lane]
                                else:
                                    total_waiting_time[junction]['w'] += prev_total_waiting_time_per_lane[junction][
                                        lane]

                # Update the waiting time per lane
                prev_total_waiting_time_per_lane = current_total_waiting_time

                # Get number of vehicles
                num_passing_vehicles_detectors = get_num_passing_vehicles_detectors(self._traci, vehicles_passed)
                data['num_passing_veh_e_w'] += num_passing_vehicles_detectors['e_w']
                data['num_passing_veh_n_s'] += num_passing_vehicles_detectors['n_s']

                # Simulate a step
                self._traci.simulationStep()

            # Process data
            data['waiting_time_veh_n_s'] = total_waiting_time['c1']['n'] + total_waiting_time['c1']['s']
            data['waiting_time_veh_e_w'] = total_waiting_time['c1']['w'] + total_waiting_time['c1']['e']

            # Insert data into the storage
            self._storage.insert_data(data)

            # Close TraCI simulation in order to start another one in the next iteration
            self._traci.close()
