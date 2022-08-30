import xml.etree.cElementTree as ET

from sumo_generators.generators.base_generator import BaseGenerator


class FlowsGenerator(BaseGenerator):
    """
    Class that generates the different flows of a SUMO simulation
    """

    def __init__(self) -> None:
        """
        FlowsGenerator initializer
        """
        # Define root element
        super().__init__(tag='routes')
        self._flows = []

    def add_flows(self, flows: list) -> None:
        """
        Add flows into a list variable

        :param flows: list with the different kind of flows
        :type flows: list
        :return None
        """
        self._flows.extend(flows)

    def store_flows(self) -> None:
        """
        Add flows to the XML object.

        :return: None
        """
        # Iterate over the flows retrieving the identifier and the flow
        for flow_id, flow in enumerate(self._flows):
            # Add tags to each flow
            flow_tag = ET.SubElement(self._root, "flow", id=str(flow_id), begin=str(flow['begin']),
                                     end=str(flow['end']), to=flow['to'], vehsPerHour=str(flow['vehsPerHour']))
            # This attribute is set in this way because the keyword "from" is reserved on Python
            flow_tag.set('from', flow['from'])

    def clean_flows(self) -> None:
        """
        Clean the XML object creating an empty "routes" tag.

        :return: None
        """
        self._flows = []
        self._root = ET.Element('routes')
