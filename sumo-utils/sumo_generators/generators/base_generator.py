from abc import ABC
import xml.etree.cElementTree as ET

from xml.dom import minidom


class BaseGenerator(ABC):
    """
    Parent abstract class for creating generators objects

    :param tag: node tag
    :type tag: str
    """

    def __init__(self, tag: str) -> None:
        self._root = ET.Element(tag)

    def write_output_file(self, output_path: str) -> None:
        """
        Write the XML object into an output file given by parameters.

        :param output_path: file directory where the TL programs will be stored
        :type output_path: str
        :return: None
        """
        # Parse the XML object to be human-readable
        xmlstr = minidom.parseString(ET.tostring(self._root)).toprettyxml(indent="   ")
        with open(output_path, "w") as f:
            # Write into the file
            f.write(xmlstr)
