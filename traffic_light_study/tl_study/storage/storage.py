import pandas as pd


class Storage:
    """
    Class for storing all the dataset information
    """

    def __init__(self):
        """
        Data fields are:

        - Simulation ID\n
        - TL ID\n
        - TL Program\n
        - Traffic type\n
        - Queue density north and south\n
        - Queue density east and west\n
        - Year\n
        - Month\n
        - Week\n
        - Day\n
        - Hour\n
        """
        # Create empty dataset
        self._data = pd.DataFrame()

    def insert_data(self, data_dict: dict):
        """
        Insert data into the dataset.

        :param data_dict: information to store into the dataset
        :type data_dict: dict
        :return:
        """
        self._data = self._data.append(data_dict, ignore_index=True)  # Ignore index to insert dict

    def to_csv(self, output_path: str):
        """
        Write the dataset into an output file.

        :param output_path: file directory where the flows will be stored
        :type output_path: str
        :return: None
        """
        # Set simulation id as the index
        if 'sim_id' in self._data:
            self._data.set_index('sim_id')
        self._data.to_csv(output_path, index=False)
