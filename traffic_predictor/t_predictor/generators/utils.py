# UTILS
def get_num_vehicles_waiting_per_queue(traci):
    """
    Retrieve from TraCI the number of vehicles waiting per each queue.
    Order is: North, East, South, West

    :param traci: TraCI instance
    :return: lists with waiting time per each orientation
    :rtype: list, list, list, list
    """
    # Retrieve the total waiting time per queue
    waiting_time_queues = get_total_waiting_time(traci)

    # Initialize queues lists
    north_waiting_time, east_waiting_time, south_waiting_time, west_waiting_time = [], [], [], []

    # Iterate over the waiting queues and store the values on its list
    for tl_k, tl_v in waiting_time_queues.items():
        waiting_times = list(waiting_time_queues[tl_k].values())
        north_waiting_time.append(waiting_times[0])
        east_waiting_time.append(waiting_times[1])
        south_waiting_time.append(waiting_times[2])
        west_waiting_time.append(waiting_times[3])

    return north_waiting_time, east_waiting_time, south_waiting_time, west_waiting_time


def get_all_lanes(traci):
    """
    Retrieve all the controlled lanes by the different traffic lights.

    :param traci: TraCI instance
    :return dict with TL ids and its controlled lanes
    :rtype dict
    """
    return {tl_id: list(dict.fromkeys(traci.trafficlight.getControlledLanes(tl_id)))
            for tl_id in traci.trafficlight.getIDList()}


def get_all_detectors(traci):
    """
    Retrieve all the detectors.

    :param traci: TraCI instance
    :return list with the detectors
    :rtype list
    """
    return traci.inductionloop.getIDList()


def get_total_waiting_time(traci):
    """
    Retrieve the waiting time of each lane related to each traffic lights.

    :param traci: TraCI instance
    :return: dict with the TL id and the waiting time per each controlled lane
    :rtype: dict
    """
    # Retrieve lanes
    lanes = get_all_lanes(traci)

    # Initialize the dict
    lanes_waiting_time = {}

    # Iterate over the different lanes
    for tl_id, tl_lanes in lanes.items():
        # Create the dict per each traffic light
        lanes_waiting_time[tl_id] = {}
        # Calculate and store the waiting time per lane
        for lane in tl_lanes:
            lanes_waiting_time[tl_id][lane] = traci.lane.getWaitingTime(lane)

    return lanes_waiting_time


def get_density_per_queue(traci):
    """
    Retrieve from TraCI the density per each queue.
    Order is: North, East, South, West

    :param traci: TraCI instance
    :return: lists with waiting time per each orientation
    :rtype: list, list, list, list
    """
    # Retrieve the total density per queue
    density_queues = get_density_per_queue(traci)

    # Initialize queues lists
    north_density, east_density, south_density, west_density = [], [], [], []

    # Iterate over the density queues and store the values on its list
    for tl_k, tl_v in density_queues.items():
        density = list(density_queues[tl_k].values())
        north_density.append(density[0])
        east_density.append(density[1])
        south_density.append(density[2])
        west_density.append(density[3])

    return north_density, east_density, south_density, west_density


def get_density_per_lane(traci):
    """
    Retrieve the density of each lane related to each traffic lights.

    :param traci: TraCI instance
    :return: dict with the TL id and the density per each controlled lane
    :rtype: dict
    """
    # Retrieve lanes
    lanes = get_all_lanes(traci)

    # Initialize the dict
    queue_density = {}

    # Iterate over the different lanes
    for tl_id, tl_lanes in lanes.items():
        # Create the dict per each traffic light
        queue_density[tl_id] = {}
        for lane in tl_lanes:
            # Calculate and store the density per lane
            queue_density[tl_id][lane] = len(traci.lane.getLastStepVehicleIDs(lane)) \
                                         / traci.lane.getLength(lane)

    return queue_density


def get_num_passing_vehicles_detectors(traci, vehicles_passed: set):
    """
    Retrieve the number of vehicles passing detectors on each direction related to each traffic lights.

    :param vehicles_passed: set with the ids of the vehicles that has been counted
    :type vehicles_passed: set
    :param traci: TraCI instance
    :return: dict with the direction and the number of vehicle passing per each controlled lane
    :rtype: dict
    """
    # Retrieve detectors
    detectors = get_all_detectors(traci)

    # Initialize the dict
    passing_veh = {'n_s': 0, 'e_w': 0}

    # Iterate over the detectors
    for detector in detectors:

        if 'n_s_loop_' in detector or 's_n_loop' in detector:
            # Get the current passing vehicles
            cur_veh = set(traci.inductionloop.getLastStepVehicleIDs(detector))

            # Calculate the difference between the sets
            not_counted_veh = cur_veh - vehicles_passed

            # If there are no counted vehicles
            if not_counted_veh:
                # Add the not counted vehicles
                vehicles_passed.update(not_counted_veh)

                # print(f'Number of passing veh from n-s {len(not_counted_veh)} on detector {detector}')

                # North-South direction
                passing_veh['n_s'] += len(not_counted_veh)

        elif 'w_e_loop_' in detector or 'e_w_loop_' in detector:
            # Get the current passing vehicles
            cur_veh = set(traci.inductionloop.getLastStepVehicleIDs(detector))

            # Calculate the difference between the sets
            not_counted_veh = cur_veh - vehicles_passed

            # If there are no counted vehicles
            if not_counted_veh:
                # Add the not counted vehicles
                vehicles_passed.update(not_counted_veh)

                # print(f'Number of passing veh from e-w {len(not_counted_veh)} on detector {detector}')

                # East-West direction
                passing_veh['e_w'] += len(not_counted_veh)

    return passing_veh


def get_traffic_light_number(traci):
    """
    Retrieve the number of traffic lights in the simulation.

    :param traci: TraCI instance
    :return: number of traffic lights
    :rtype: int
    """
    return len(traci.trafficlight.getIDList())
