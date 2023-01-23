from statistics import mean


class TrafficLightInfoStorage:
    """
    Traffic Light Info Storage  class to gather all the traffic related information 
    """

    def __init__(self, tl_id: str, actual_program: str = '', lanes: list = None) -> None:
        """
        TrafficInfoStorage initializer

        :param tl_id: traffic light identifier
        :type tl_id: str
        :param actual_program: actual traffic light program. Default to ''.
        :type actual_program: str
        :param lanes: lanes names list
        :type lanes: list
        :return: None
        """
        # Initialize non-default values
        self._lanes = [] if not lanes else lanes

        # Vehicles passed and turning vehicles passed on the traffic light
        self._vehicles_passed, self._turning_vehicles_passed = set(), set()
        # Actual program and traffic light id
        self._actual_program, self._tl_id = actual_program, tl_id

        # Initialize the historical dictionary and current temporal window
        self._historical_info, self._cur_temporal_window = {}, 0

        # Initialize the first historical info
        self.create_historical_traffic_info(self._cur_temporal_window)

    def create_historical_traffic_info(self, temporal_window: int, lane_info: dict = None) -> None:
        """
        Creates a new entry for the historical info for the timestep

        :param temporal_window: current info temporal window
        :type temporal_window: int
        :param lane_info: number of passing vehicles, waiting time and turning vehicles per lane.
        :type lane_info: dict

        :return: None
        """
        # If lane info does not have information
        if not lane_info:
            # Initialize passing vehicles, waiting time and turning vehicles per lane
            lane_info = {lane: {'num_passing_veh': 0, 'waiting_time_veh': 0.0, 'occupancy': [], 'CO2_emission': [],
                                 'CO_emission': [], 'HC_emission': [], 'PMx_emission': [], 'NOx_emission': [],
                                 'noise_emission': []} for lane in self._lanes} if not lane_info else lane_info

        # Store information into the dict
        self._historical_info[temporal_window] = {'contextual_info': lane_info,
                                                  'date_info': None,
                                                  'actual_program': self._actual_program}

    def increase_turning_vehicles(self, turn: str) -> None:
        """
        Increase the number of turning vehicles by 1 on the given turn

        :param turn: turn direction
        :type turn: str
        :return: None
        """
        self._historical_info[self._cur_temporal_window]['turning_vehicles'][turn] += 1

    def append_turning_vehicle(self, vehicle_id: str) -> None:
        """
        Append a vehicle to the list of turning vehicles of the traffic light

        :param vehicle_id: vehicle identifier
        :type vehicle_id: str
        :return: None
        """
        self._turning_vehicles_passed.add(vehicle_id)

    def is_vehicle_turning_counted(self, vehicle_id: str) -> bool:
        """
        Check if a turning vehicles has been counted previously

        :param vehicle_id: vehicle identifier
        :type vehicle_id: str
        :return: True if it is counted, False otherwise
        :rtype: bool
        """
        return vehicle_id in self._turning_vehicles_passed

    """ UTILS """

    def insert_date_info(self, temporal_window: int, date_info: dict) -> None:
        """
        Insert date information to current traffic light info at a given temporal window

        :param temporal_window: temporal window identifier
        :type temporal_window: int
        :param date_info: simulation date information
        :type date_info: dict
        :return: None
        """

        # Update the date info for the current traffic light at a given temporal window
        self._historical_info[temporal_window]['date_info'] = date_info

    def increase_temporal_window(self):
        self._cur_temporal_window += 1

    """ EXTERNAL TRAFFIC COMPONENTS UTILS """

    def get_processed_contextual_info(self, temporal_window: int) -> dict:
        """
        Process the values of contextual info calculating the average and sum values

        :param temporal_window: temporal window
        :type temporal_window: int
        :return: dict with passing vehicles on NS and EW direction
        :rtype: dict
        """

        # Create a list based on lane information
        contextual_lane_info = [{'tl_id': self._tl_id, 'lane': lane_name,
                                  'waiting_time_veh': lane_info['waiting_time_veh'],
                                  'num_passing_veh': lane_info['num_passing_veh'],
                                  'avg_lane_occupancy': mean(lane_info['occupancy']),
                                  'avg_CO2_emission': mean(lane_info['CO2_emission']),
                                  'avg_CO_emission': mean(lane_info['CO_emission']),
                                  'avg_HC_emission': mean(lane_info['HC_emission']),
                                  'avg_PMx_emission': mean(lane_info['PMx_emission']),
                                  'avg_NOx_emission': mean(lane_info['NOx_emission']),
                                  'avg_noise_emission': mean(lane_info['noise_emission'])}
                                 for lane_name, lane_info in self._historical_info[temporal_window]
                                 ['contextual_info'].items()]

        return {'info': contextual_lane_info}

    def get_traffic_analyzer_info(self, temporal_window: int) -> dict:
        """
        Get the traffic analyzer required information (only passing vehicles)

        :param temporal_window: temporal window
        :type temporal_window: int
        :return: dict with passing vehicles on NS and EW direction
        :rtype: dict
        """
        # Iterate over all the lanes and retrieve its number of passing vehicles
        return {lane_name: {'num_passing_veh': lane_info['num_passing_veh']}
                for lane_name, lane_info in self._historical_info[temporal_window]['contextual_info'].items()}

    def get_traffic_predictor_info(self, temporal_window: int) -> dict:
        """
        Get the traffic predictor required information based on the type of traffic predictor

        :param temporal_window: temporal window
        :type temporal_window: int
        :return: dict with date info
        :rtype: dict
        """
        # Get date info
        date_info = self._historical_info[temporal_window]['date_info']

        # Get all roads names with the date info
        traffic_predictor_info = {road: date_info for road in list(dict(self._historical_info[temporal_window]
                                                                        ['contextual_info']).keys())}
        return traffic_predictor_info

    def get_turn_predictor_info(self) -> None:
        pass

    """ CLASS ATTRIBUTES UTILS """

    def increase_passing_vehicles(self, lane: str, num_veh: int) -> None:
        """
        Increase the number of passing vehicles on the lane given at the current temporal window

        :param lane: input lane which is the name of the road.
        :type lane: str
        :param num_veh: number of vehicles
        :type num_veh: int
        :return: None
        """
        self._historical_info[self._cur_temporal_window]['contextual_info'][lane]['num_passing_veh'] += num_veh

    def increase_waiting_time(self, lane: str, waiting_time: float) -> None:
        """
        Increase the waiting time on the given direction at the current temporal window

        :param lane: input lane which is the name of the road.
        :type lane: str
        :param waiting_time: waiting time
        :type waiting_time: float
        :return: None
        """
        self._historical_info[self._cur_temporal_window]['contextual_info'][lane]['waiting_time_veh'] += waiting_time

    def update_passing_vehicles(self, passing_veh: set) -> None:
        """
        Append new passing vehicles

        :param passing_veh: new passing vehicles
        :type passing_veh: set
        :return: None
        """
        self._vehicles_passed.update(passing_veh)

    def remove_passed_vehicles(self, vehicles: set) -> None:
        """
        Remove passed vehicles from both "vehicles_passed" and "turning_vehicles_passed"

        :param vehicles: vehicles that has passed
        :type vehicles: str
        :return: None
        """
        self._vehicles_passed.difference_update(vehicles)
        self._turning_vehicles_passed.difference_update(vehicles)

    def get_traffic_info_by_temporal_window(self, temporal_window: int) -> dict:
        """
        Get traffic info related to a given temporal window

        :param temporal_window: temporal window to retrieve the information
        :type temporal_window: int
        :return: historical traffic information
        :rtype: dict
        """
        return self._historical_info[temporal_window]

    def append_item_on_list_lane(self, lane: str, name: str, value: float) -> None:
        """
        Append a new value into a list with the given name on the lane historical info

        :param lane: lane name
        :type lane: str
        :param name: value name
        :type name: str
        :param value: item value
        :type value: str
        :return: None
        """
        self._historical_info[self._cur_temporal_window]['contextual_info'][lane][name].append(value)

    """ SETTERS AND GETTERS """

    @property
    def cur_temporal_window(self) -> int:
        """
        Traffic Light Info Storage current temporal window getter

        :return: current temporal window
        :rtype: int
        """
        return self._cur_temporal_window

    @cur_temporal_window.setter
    def cur_temporal_window(self, cur_temporal_window: int) -> None:
        """
        Traffic Light Info Storage current temporal window setter

        :param cur_temporal_window: new temporal window
        :type cur_temporal_window: int
        :return: None
        """
        self._cur_temporal_window = cur_temporal_window

    @property
    def historical_info(self) -> dict:
        """
        Traffic Light Info Storage historical info

        :return: historical info
        :rtype: dict
        """
        return self._historical_info

    @property
    def vehicles_passed(self) -> set:
        """
        Traffic Light Info Storage  vehicles passed getter

        :return: vehicles passed
        :rtype: set
        """
        return self._vehicles_passed

    @property
    def turning_vehicles_passed(self) -> set:
        """
        Traffic Light Info Storage turning vehicles passed getter
 
        :return: turning vehicles passed
        :rtype: dict
        """
        return self._turning_vehicles_passed

    @property
    def lanes(self) -> list:
        """
        Traffic Light Info Storage lanes getter

        :return: lanes ids
        :rtype: list
        """
        return self._lanes

    @lanes.setter
    def lanes(self, lanes: list) -> None:
        """
        Traffic Light Info Storage lanes setter

        :param lanes: lanes names list
        :type lanes: list
        :return: None
        """
        self._lanes = lanes

    @property
    def actual_program(self) -> str:
        """
        Traffic Light Info Storage  actual program getter

        :return: actual program
        :rtype: str
        """
        return self._actual_program
