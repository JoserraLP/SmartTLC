import optparse
import os
import stat

from sumo_generators.config_generator import generate_flow_file
from constants import CALENDAR_PATTERN_FILE, ADAPTATION_COMPONENTS, ADAPTATION_FILE_SCHEMA


def get_num_parent_folders(folder_name: str):
    """
    :param folder_name: folder name to be searched on parents folder.
    :type folder_name: str
    :return: number of parents folder
    """

    # Directory from where search starts (Actual one); found flag and counter of folders (started to 1 because of the
    # location of this script)
    cur_dir, found, num_folders = os.getcwd(), False, 1

    # Iterate until the folder is found
    while not found:
        # Retrieve list of files and parent dir
        file_list, parent_dir = os.listdir(cur_dir), os.path.dirname(cur_dir)
        # Check if folder is in list
        if folder_name in file_list:
            found = True
        else:
            # Increase counter and update the directory
            num_folders += 1
            if cur_dir == parent_dir:  # if dir is root dir
                break
            else:
                cur_dir = parent_dir

    return num_folders


def get_options():
    """
    Define options for the executable script.

    :return: options
    :rtype: object
    """
    optParser = optparse.OptionParser()
    optParser.add_option("-o", "--output-dir", dest="output_directory", action='store',
                         help="output directory location")

    # Topology parameters
    topology_group = optparse.OptionGroup(optParser, "Network topology parameters",
                                          "Define network related variables")
    topology_group.add_option("-c", "--columns", dest="cols", action='store',
                              help="grid topology columns. Actual dimension + 2")
    topology_group.add_option("-r", "--rows", dest="rows", action='store',
                              help="grid topology rows. Actual dimension + 2")
    topology_group.add_option("-l", "--lanes", dest="lanes", action='store', help="grid topology lanes.")

    # Traffic time pattern group
    traffic_pattern_group = optparse.OptionGroup(optParser, "Time pattern parameters",
                                                 "Select between date interval or specific time pattern")
    traffic_pattern_group.add_option("-t", "--time-pattern", dest="time_pattern_path", action='store',
                                     help="time pattern to create the flows.")

    traffic_pattern_group.add_option("-d", "--dates", dest="dates", action="store",
                                     help="calendar dates from start to end to simulate. Format is "
                                          "dd/mm/yyyy-dd/mm/yyyy.")

    # Turn pattern group
    turn_pattern_group = optparse.OptionGroup(optParser, "Turn pattern parameters",
                                                 "Set the turn pattern file if required")
    turn_pattern_group.add_option("--turn-pattern", dest="turn_pattern_path", action='store',
                                     help="turn pattern of the simulation.")

    options, args = optParser.parse_args()
    return options


if __name__ == '__main__':

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Output dir
    output_dir = exec_options.output_directory

    # Check if directory does not exist, to create it
    if output_dir and not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # Get number of parent folders to "docker-utils" component:
    num_parent_folders = get_num_parent_folders('docker-utils')

    # Retrieve topology parameters values
    cols, rows, lanes = int(exec_options.cols), int(exec_options.rows), int(exec_options.lanes)

    # Retrieve traffic time pattern
    time_pattern_path = exec_options.time_pattern_path
    dates = exec_options.dates
    turn_pattern_path = exec_options.turn_pattern_path

    # 1. We need to create the flows.rou.xml file based on the time pattern and network topology
    # Execute the SUMO utils generator script
    if dates:
        # Generate flow file based on date interval
        generate_flow_file(dates=dates, flows_path=output_dir + "/flows.rou.xml",
                           rows=rows, cols=cols, calendar_pattern_file=CALENDAR_PATTERN_FILE)
    elif time_pattern_path:
        # Generate flow file based on time pattern
        generate_flow_file(time_pattern_path=time_pattern_path, flows_path=output_dir + "/flows.rou.xml",
                           rows=rows, cols=cols)

    # 2. Create sh file per each adaptation
    for adaptation, add_components in ADAPTATION_COMPONENTS.items():
        # Retrieve file schema, set the adaptation name and initialize the TLC pattern
        file_str, adaptation_name, tlc_pattern = ADAPTATION_FILE_SCHEMA, 'example_' + adaptation, ''

        # If date interval set pattern parameter
        if dates:
            tlc_pattern = 'date#' + dates
        # If time pattern set pattern parameter
        elif time_pattern_path:
            # Replace ../ for /etc/ -> For Docker-compose generation
            tlc_pattern = 'pattern#' + time_pattern_path.replace('../', '/etc/')

        if turn_pattern_path:
            # Replace ../ for /etc/ -> For Docker-compose generation
            tlc_pattern += ':turn#' + turn_pattern_path.replace('../', '/etc/')

        # Define output executable sh file
        file_name = output_dir + '/' + adaptation_name + ".sh"
        # Create each sh file
        with open(file_name, "w") as adaptation_file:
            adaptation_file.write(file_str.format(num_parent_folders=num_parent_folders*'../',
                                                  tlc_pattern=tlc_pattern, rows=rows, cols=cols, lanes=lanes,
                                                  exp_file=f'grid_{rows}x{cols}_{adaptation_name}.xlsx',
                                                  add_components=add_components))
        # Get sh file current permissions
        st = os.stat(file_name)
        # Update the permissions to be executable
        os.chmod(file_name, st.st_mode | stat.S_IEXEC)
