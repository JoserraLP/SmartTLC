import copy


class TrafficLightInfoStorage:
    """
    Traffic Light Info Storage  class to gather all the traffic related information 
    """

    def __init__(self, actual_program: str = '', topology_info: dict = None, roads: list = None) -> None:
        """
        TrafficInfoStorage initializer

        :param actual_program: actual traffic light program. Default to ''.
        :type actual_program: str
        :param topology_info: additional topology info about the traffic light storage. Default is empty
        :type topology_info: dict
        :param roads: roads names list
        :type roads: list
        :return: None
        """
        # Initialize non-default values
        self._topology_info = {} if not topology_info else topology_info
        self._roads = [] if not roads else roads

        # Vehicles passed and turning vehicles passed on the traffic light
        self._vehicles_passed, self._turning_vehicles_passed = set(), set()
        # Actual program
        self._actual_program = actual_program

        # Initialize the historical dictionary and current temporal window
        self._historical_info, self._cur_temporal_window = {}, 0

    def create_historical_traffic_info(self, temporal_window: int, passing_veh_n_s: int = 0, passing_veh_e_w: int = 0,
                                       waiting_time_veh_n_s: int = 0, waiting_time_veh_e_w: int = 0,
                                       turning_forward: int = 0, turning_right: int = 0, turning_left: int = 0) -> None:
        """
        Creates a new entry for the historical info for the timestep

        :param temporal_window: current info temporal window
        :type temporal_window: int
        :param passing_veh_n_s: number of passing vehicles on NS direction. Default to 0.
        :type passing_veh_n_s: int
        :param passing_veh_e_w: number of passing vehicles on EW direction. Default to 0.
        :type passing_veh_e_w: int
        :param waiting_time_veh_n_s: waiting time on NS direction. Default to 0.
        :type waiting_time_veh_n_s: int
        :param waiting_time_veh_e_w: waiting time on EW direction. Default to 0.
        :type waiting_time_veh_e_w: int
        :param turning_forward: number of vehicles going forward. Default to 0.
        :type turning_forward: int
        :param turning_right: number of vehicles turning right. Default to 0.
        :type turning_right: int
        :param turning_left: number of vehicles turning left. Default to 0.
        :type turning_left: int

        :return: None
        """
        self._historical_info[temporal_window] = {'passing_veh_n_s': passing_veh_n_s,
                                                  'passing_veh_e_w': passing_veh_e_w,
                                                  'waiting_time_veh_n_s': waiting_time_veh_n_s,
                                                  'waiting_time_veh_e_w': waiting_time_veh_e_w,
                                                  'turning_vehicles':
                                                      {'forward': turning_forward,
                                                       'right': turning_right,
                                                       'left': turning_left
                                                       },
                                                  'date_info': None
                                                  }

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

        self._cur_temporal_window = temporal_window

        # Update the date info for the current traffic light at a given temporal window
        self._historical_info[temporal_window]['date_info'] = date_info

    """ EXTERNAL TRAFFIC COMPONENTS UTILS """

    def get_publish_info(self, temporal_window: int) -> dict:
        """
        Process the traffic_info and date_info dictionaries to be formatted to a valid Telegraf schema

        :param temporal_window: temporal window
        :type temporal_window: int
        :return: dict with passing vehicles on NS and EW direction
        :rtype: dict
        """
        # Copy the value from the historical info of the current timestep
        traffic_info_dict = copy.deepcopy(self._historical_info[temporal_window])

        # Add the actual program and the roads info
        traffic_info_dict.update({'actual_program': self._actual_program, 'roads': self._roads})

        return traffic_info_dict

    def get_traffic_analyzer_info(self, temporal_window: int) -> dict:
        """
        Get the traffic analyzer required information (only passing vehicles per direction)

        :param temporal_window: temporal window
        :type temporal_window: int
        :return: dict with passing vehicles on NS and EW direction
        :rtype: dict
        """
        return {'passing_veh_n_s': self._historical_info[temporal_window]['passing_veh_n_s'],
                'passing_veh_e_w': self._historical_info[temporal_window]['passing_veh_e_w']}

    def get_traffic_predictor_info(self, temporal_window: int, date: bool = True) -> None:
        """
        Get the traffic predictor required information based on the type of traffic predictor

        :param temporal_window: temporal window
        :type temporal_window: int
        :param date: flag enabling date-based traffic predictors
        :type date: bool
        :return: dict with passing vehicles on NS and EW direction
        :rtype: dict
        """

        # Store the date information
        traffic_predictor_info = dict(self._historical_info[temporal_window]['date_info'])

        # If it is also contextual based
        if not date:
            traffic_predictor_info.update(self.get_traffic_analyzer_info(temporal_window))

        return traffic_predictor_info

    def get_turn_predictor_info(self) -> None:
        pass

    """ CLASS ATTRIBUTES UTILS """

    def increase_passing_vehicles(self, direction: str, num_veh: int) -> None:
        """
        Increase the number of passing vehicles on the direction given at the current temporal window

        :param direction: direction. It can be "n_s" or "e_w"
        :type direction: str
        :param num_veh: number of vehicles
        :type num_veh: int
        :return: None
        """
        self._historical_info[self._cur_temporal_window]['passing_veh_' + direction] += num_veh

    def increase_waiting_time(self, direction: str, waiting_time: float) -> None:
        """
        Increase the waiting time on the given direction at the current temporal window

        :param direction: direction. It can be "n_s" or "e_w"
        :type direction: str
        :param waiting_time: waiting time
        :type waiting_time: float
        :return: None
        """
        self._historical_info[self._cur_temporal_window]['waiting_time_veh_' + direction] += waiting_time

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

    def get_traffic_info_by_temporal_window(self, temporal_window: int):
        return self._historical_info[temporal_window]

    """ SETTERS AND GETTERS """

    '''
    @property
    def temporal_window(self) -> int:
        """
        Traffic Light Info Storage current temporal window getter

        :return: temporal window
        :rtype: int
        """
        return self._temporal_window

    @temporal_window.setter
    def temporal_window(self, temporal_window: int) -> None:
        """
        Traffic Light Info Storage current temporal window setter

        :param temporal_window: new temporal window
        :type temporal_window: int
        :return: None
        """
        self._temporal_window = temporal_window
    '''

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
    def turning_vehicles_passed(self) -> dict:
        """
        Traffic Light Info Storage turning vehicles passed getter
 
        :return: turning vehicles passed
        :rtype: dict
        """
        return self._turning_vehicles_passed

    @property
    def roads(self) -> list:
        """
        Traffic Light Info Storage roads getter

        :return: roads ids
        :rtype: list
        """
        return self._roads

    @roads.setter
    def roads(self, roads: list) -> None:
        """
        Traffic Light Info Storage roads setter

        :param roads: roads names list
        :type roads: list
        :return: None
        """
        self._roads = roads

    @property
    def actual_program(self) -> str:
        """
        Traffic Light Info Storage  actual program getter

        :return: actual program
        :rtype: str
        """
        return self._actual_program

    @property
    def topology_info(self) -> dict:
        """
        Traffic Light Info Storage topology info getter

        :return: topology info
        :rtype: dict
        """
        return self._topology_info
