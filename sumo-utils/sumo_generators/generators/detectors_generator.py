import xml.etree.cElementTree as ET

from tl_controller.generators.base_generator import BaseGenerator


class DetectorsGenerator(BaseGenerator):
    """
    Class that generates the different detectors of a SUMO simulation
    """

    def __init__(self) -> None:
        """
        DetectorGenerator initializer
        """
        # Define root element
        super().__init__(tag='additional')
        self._detectors = []

    def add_detectors(self, detectors: list) -> None:
        """
        Add detector into a list variable

        :param detectors: list with the different detectors
        :type detectors: list
        :return None
        """
        self._detectors.extend(detectors)

    def store_detectors(self) -> None:
        """
        Add detectors to the XML object.

        :return: None
        """
        # Iterate over the detectors retrieving the identifier and the flow
        for detector in self._detectors:
            # Add tags to each detector
            ET.SubElement(self._root, "inductionLoop", id=str(detector['id']), lane=str(detector['lane']),
                          pos=str(detector['pos']), freq=str(detector['freq']), file=str(detector['file']))

    def clean_detectors(self) -> None:
        """
        Clean the XML object creating an empty "additional" tag.

        :return: None
        """
        self._detectors = []
        self._root = ET.Element('additional')
