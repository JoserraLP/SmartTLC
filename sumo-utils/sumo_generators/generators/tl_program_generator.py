import xml.etree.cElementTree as ET

from tl_controller.generators.base_generator import BaseGenerator


class TrafficLightProgramGenerator(BaseGenerator):
    """
    Class that generates the traffic lights programs in an additional file
    """

    def __init__(self, topology_rows, topology_cols):
        """
        TrafficLightProgramGenerator initializer
        """
        # Define root element
        super().__init__(tag='additional')

        # Define traffic lights ids
        self._traffic_light_ids = [f'c{i}' for i in range(1, topology_rows*topology_cols+1)]

    def add_static_program(self, phases: list, program_id: str = 'static_program', offset: int = '0'):
        """
        Add a static program with given phases.

        :param phases: phases for the static program
        :type phases: list
        :param program_id: program identifier. Default to 'static_program'.
        :type program_id: str
        :param offset: program offset. Default to 0.
        :type offset: int
        :return: None
        """
        # Create the same static program for all the traffic lights
        for traffic_light in self._traffic_light_ids:
            # Define the tl_logic tag
            tl_logic = ET.SubElement(self._root, "tlLogic", id=str(traffic_light), programID=program_id,
                                     type="static", offset=offset)

            # Iterate over the phases and store them
            for phase in phases:
                ET.SubElement(tl_logic, "phase", duration=phase['duration'], state=phase['state'])

    def add_actuated_program(self, phases: list, params_type: str = "", params=None):
        """
        Add a static program with given phases.

        :param phases: phases for the actuated program
        :type phases: list
        :param params_type: type of the parameters
        :type params_type: str
        :param params: actuated program params
        :type params: list
        :return:  None
        """
        # Select different actuated program identifier
        programID = "actuated_program"
        if params_type == "time_gap":
            programID += "_time_gap"
        elif params_type == "time_loss":
            programID += "_time_loss"

        # Create the same static program for all the traffic lights
        for traffic_light in self._traffic_light_ids:
            # Define the tl_logic tag
            tl_logic = ET.SubElement(self._root, "tlLogic", id=str(traffic_light), programID=programID,
                                     type="actuated")

            # Add the params for the "time_gap" and "time_loss" variants
            if params:
                for param in params:
                    ET.SubElement(tl_logic, "param", key=param[0], value=param[1])

            # Iterate over the phases and store them
            for phase in phases:
                ET.SubElement(tl_logic, "phase", duration=phase['duration'], minDur=phase['minDur'],
                              maxDur=phase['maxDur'], state=phase['state'])
