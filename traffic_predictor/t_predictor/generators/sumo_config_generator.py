import xml.etree.cElementTree as ET

from t_predictor.generators.base_generator import BaseGenerator


class SumoConfigGenerator(BaseGenerator):
    """
    Class that generates the SUMO configuration file
    """

    def __init__(self):
        """
        SumoConfigGenerator initializer
        """
        # Define root element
        super().__init__(tag='configuration')
        # Set different attributes required by SUMO
        self._root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        self._root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/sumoConfiguration.xsd")

    def set_input_files(self, files: dict):
        """
        Add files directories to the input tag.

        :param files: input files required to simulate in SUMO (network, flows, additional files...)
        :type files: dict
        :return: None
        """
        # Define the input tag
        input_tag = ET.SubElement(self._root, "input")
        # Iterate over the different input files and store them
        for file_tag, file_value in files.items():
            ET.SubElement(input_tag, file_tag, value=file_value)

    def set_begin_time(self, value: int = 0):
        """
        Set the begin time for the simulation.

        :param value: begin time. Default to 0
        :type value: int
        :return: None
        """
        # Define the time tag
        time = ET.SubElement(self._root, "time")
        # Set the value
        ET.SubElement(time, "begin", value=str(value))

    def set_report_policy(self, policy_values: dict):
        """
        Add the report policy.

        :param policy_values: different policies such as "verbose" or "no-step-log"
        :type policy_values: dict
        :return: None
        """
        # Define the report tag
        report = ET.SubElement(self._root, "report")
        # Iterate over the policies retrieving its values
        for policy_id, policy_value in policy_values.items():
            ET.SubElement(report, policy_id, value=policy_value)
