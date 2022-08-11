from t_predictor.visualization.visualizer import Visualizer
from t_predictor.visualization.utils import generate_random_palette
from t_predictor.static.constants import DEFAULT_OUTPUT_FILE, NUM_TRAFFIC_TYPES
import pandas as pd


class ConsoleVisualizer:
    """
    Class for showing options to create different plots from a dataset.
    """

    def __init__(self):
        """
        ConsoleVisualizer initializer
        """
        # Define the different prompts as the menu or the dataset, plot, attributes and selection.
        self._menu = 'This is the visualization CLI, please insert the desired action: \n' \
                     '1. Select dataset (Mandatory at least first time)\n' \
                     '2. Select kind of plot\n' \
                     '3. Exit\n' \
                     'Your option: '

        self._select_dataset = f'Please insert the directory where the dataset (.csv) is stored. Default is ' \
                               f' {DEFAULT_OUTPUT_FILE}\n'

        self._select_plot = 'Please select one of the following plots (introducing its number): \n' \
                            '1. Box plot\n' \
                            '2. Scatter plot\n' \
                            '3. Pair plot\n' \
                            '4. Bar plot\n' \
                            '5. Line plot\n' \
                            '6. Exit\n' \
                            'Your option: '

        self._select_attributes = 'Please insert the X-axis field, Y-axis field and Hue from the next options, ' \
                                  'split by comma:\n'

        self._select_hue_attribute = 'Please insert the Hue field from the next options: \n'

        # Define a dataframe for storing the dataset columns
        self._dataset_columns = pd.DataFrame()

        # Define the visualizer object
        self._visualizer = Visualizer()

    def execute(self) -> None:
        """
        Execute the command prompt application.

        :return: None
        """
        # Define a flag for the first time
        first_time = True

        # First time we remove the option of setting the attributes
        selected_option = int(input(self._menu.replace('2. Select kind of plot\n', '')))

        # Until the selection option is "Exit" (Number 3)
        while selected_option != 3:
            # Select a dataset
            if selected_option == 1:
                self.select_dataset()
                # Update flag
                first_time = False
            # Select the plot
            elif selected_option == 2:
                self.select_plot()
            else:
                # Show error message
                print('Please insert a valid value')

            # Retrieve the next option, showing a different message depending on the execution number
            if first_time:
                selected_option = int(input(self._menu.replace('2. Select kind of plot\n', '')))
            else:
                selected_option = int(input(self._menu))

        print("Bye bye!!")

    def select_dataset(self) -> None:
        """
        Load the dataset indicated by the user and define the visualizer class.

        :return: None
        """
        # Retrieve dataset input file. Replacing whitespaces
        dataset_file = input(self._select_dataset).replace(' ', '')

        # If empty, set default value
        if dataset_file == '':
            dataset_file = DEFAULT_OUTPUT_FILE

        # Load dataset in order to retrieve the columns names
        self._dataset_columns = pd.read_csv(dataset_file).columns

        # Columns string
        columns = ', '.join(self._dataset_columns)

        # Create the attributes messages
        self._select_attributes += columns + '\nYour option: '
        self._select_hue_attribute += columns + '\nYour option: '

        # Load dataset into the visualizer
        self._visualizer.load_dataset(dataset_file)

        print(f'Dataset {dataset_file} loaded successfully\n')

    def select_plot(self) -> None:
        """
        Retrieve the plot selected by the user and the required attributes.

        :return: None
        """
        # Retrieve plot
        plot = input(self._select_plot)

        while plot == '':
            # If empty show a message
            print("Please, introduce a valid value")
            plot = input(self._select_plot)

        # Parse to int
        plot = int(plot)

        # Maximum possible values of palette is 9 -> Traffic type
        palette = generate_random_palette(NUM_TRAFFIC_TYPES)

        # Create plots, depending on the selection
        if plot in [1, 2, 4, 5]:
            # Retrieve same attributes (x, y, hue)
            x, y, hue = self.select_attributes()

            if plot == 1:  # Box plot
                self._visualizer.create_box_plot(x, y, hue, palette)
            elif plot == 2:  # Scatter plot
                self._visualizer.create_scatter_plot(x, y, hue, palette)
            elif plot == 4:  # Bar plot
                self._visualizer.create_bar_plot(x, y, hue, palette)
            elif plot == 5:  # Line plot
                self._visualizer.create_line_plot(x, y, hue, palette)
        elif plot == 3:  # Pair plot
            # Retrieve on hue attribute
            self._visualizer.create_pair_plot(hue=input(self._select_hue_attribute), palette=palette)
        elif plot == 6:  # Exit the method
            return
        else:  # Error message
            print("Please, introduce a valid option")
            # Recall the method
            self.select_plot()

    def select_attributes(self) -> None:
        """
        Select the attributes that will be plotted.

        :return: x-axis, y-axis and hue values
        :rtype: str, str, str
        """
        # Retrieve attributes
        attributes = input(self._select_attributes).lower().replace(' ', '').split(',')

        # While there are no three values still retrieve
        while len(attributes) != 3:
            print("Please, introduce three values.\n")
            attributes = input(self._select_attributes).lower().replace(' ', '').split(',')

        # While the selected options are not valid columns
        while not all(attribute in self._dataset_columns.tolist() for attribute in attributes):
            print(f"Please, introduce valid values.\n Options are: {', '.join(self._dataset_columns)}")
            attributes = input(self._select_attributes).lower().replace(' ', '').split(',')

        # Retrieve the three values
        x, y, hue = attributes[:3]

        return x, y, hue
