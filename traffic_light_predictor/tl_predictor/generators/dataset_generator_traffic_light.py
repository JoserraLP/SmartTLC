import traci

from tl_predictor.generators.dataset_generator import DatasetGenerator
from tl_predictor.generators.utils import get_num_vehicles_waiting_per_queue


class TrafficTypeGenerator(DatasetGenerator):
    """
    Dataset generator from the TraCI simulations
    """

    def __init__(self, sumo_conf, num_sim: int = 0):
        """
        TraCISimulator initializer.

        :param sumo_conf: SUMO configuration
        :param num_sim: number of simulations. Default is 0.
        :type num_sim: int
        """

        # SUMO configuration files
        super().__init__(sumo_conf)

        self._num_sim = num_sim

        # Calculate the number of simulation per each TL program
        self._sim_portions = num_sim / self._num_tl_programs

    def simulate(self):
        """
        Perform the dataset generation with number of simulations by simulating with TraCI.

        :return: None
        """
        # Loop for all the simulations
        for sim_id in range(self._num_sim):

            print(f"SIMULATION {sim_id}")

            # Retrieve simulation TL program
            tl_program = self.select_tl_program(sim_id)
            # Retrieve simulation traffic type
            traffic_type = self.select_traffic_type(sim_id)

            # Initialize basic data schema
            data = {'sim_id': sim_id, 'tl_id': 'c1', 'tl_program': tl_program, 'traffic_type': traffic_type,
                    'waiting_veh_n': 0, 'waiting_veh_e': 0, 'waiting_veh_s': 0, 'waiting_veh_w': 0}

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

            # Traci simulation
            # Iterate until there are no more vehicles
            while self._traci.simulation.getMinExpectedNumber() > 0:
                # Retrieve all the info

                # Density
                north_waiting_time, east_waiting_time, south_waiting_time, west_waiting_time = \
                    get_num_vehicles_waiting_per_queue(self._traci)

                # Increase waiting values per queue.
                # Access to first index ([0]) as it is a list
                data['waiting_veh_n'] += north_waiting_time[0]
                data['waiting_veh_e'] += east_waiting_time[0]
                data['waiting_veh_s'] += south_waiting_time[0]
                data['waiting_veh_w'] += west_waiting_time[0]

                # Simulate a step
                self._traci.simulationStep()

            # Insert data into the storage
            self._storage.insert_data(data)

            # Close TraCI simulation in order to start another one in the next iteration
            self._traci.close()

    def select_tl_program(self, sim_id: int):
        """
        Return the selected TL program depending on the simulation number.

        :param sim_id: simulation identifier
        :type sim_id: int
        :return: tl program
        :rtype: str
        """
        program_id = ""

        # Define the program depending on the simulation number and order
        if sim_id < self._sim_portions:
            # Static sim
            program_id = "static_program"
        elif self._sim_portions <= sim_id < self._sim_portions * 2:
            # Actuated
            program_id = "actuated_program"
        elif self._sim_portions * 2 <= sim_id < self._sim_portions * 3:
            # Actuated with time gap
            program_id = "actuated_program_time_gap"
        elif self._sim_portions * 3 <= sim_id < self._sim_portions * 4:
            # Actuated with time loss
            program_id = "actuated_program_time_loss"

        return program_id
