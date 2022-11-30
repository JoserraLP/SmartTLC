import argparse
import os
import stat
from pathlib import Path

from sumo_generators.static.constants import DEFAULT_NODES_FILENAME, DEFAULT_EDGES_FILENAME, DEFAULT_NET_FILENAME, \
    DEFAULT_DET_FILENAME, DEFAULT_TLL_FILENAME, DEFAULT_ROUTE_FILENAME, DEFAULT_CONFIG_FILENAME

from argparse_types import check_file, check_dimension, check_valid_format, check_os
from constants import *


def get_num_parent_folders(folder_name: str) -> int:
    """
    Calculate the number of parent folders where a given folder is from the current directory.

    :param folder_name: folder name to be searched on parents folder.
    :type folder_name: str
    :return: number of parents folder
    :rtype: int
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
            if cur_dir == parent_dir:  # If dir is root dir
                break
            else:  # Otherwise update the current directory
                cur_dir = parent_dir

    return num_folders


def get_options():
    """
    Get options for the executable script.

    :return: Arguments options
    """
    # Create the Argument Parser
    arg_parser = argparse.ArgumentParser(description='Script to generate an experiment based on the information '
                                                     'provided by parameters. This script generates the folder, each '
                                                     'adaptation approach bash and the vehicles flows related.')

    # Define the arguments options
    arg_parser.add_argument("-o", "--output-dir", dest="output_directory", action='store',
                            help="output directory location.", required=True)

    arg_parser.add_argument("--os", dest="os", action='store', default="ubuntu",
                            help="operative system. Can be windows or ubuntu (default).", type=check_os)

    # Topology parameters
    topology_group = arg_parser.add_argument_group("Network topology parameters",
                                                   description="Define network related variables")
    topology_group.add_argument("-c", "--columns", dest="cols", action='store',
                                help="grid topology columns. Must be greater than 1.", required=True,
                                type=check_dimension)
    topology_group.add_argument("-r", "--rows", dest="rows", action='store',
                                help="grid topology rows. Must be greater than 1.", required=True, type=check_dimension)
    topology_group.add_argument("-l", "--lanes", dest="lanes", action='store', help="grid topology lanes. "
                                                                                    "Must be greater than 1.",
                                required=True, type=check_dimension)

    # Traffic time pattern group
    traffic_pattern_group = arg_parser.add_argument_group("Time pattern parameters",
                                                          description="Select between date interval or specific time "
                                                                      "pattern. One must be selected")
    traffic_pattern_group.add_argument("-t", "--time-pattern", dest="time_pattern_path", action='store',
                                       help="time pattern to load the flows.", type=check_file)

    traffic_pattern_group.add_argument("-d", "--dates", dest="dates", action="store",
                                       help="calendar dates from start to end to simulate. Format is "
                                            "dd/mm/yyyy-dd/mm/yyyy.", type=check_valid_format)

    # Turn pattern group
    turn_pattern_group = arg_parser.add_argument_group("Turn pattern parameters",
                                                       description="Set the turn pattern file if required")
    turn_pattern_group.add_argument("--turn-pattern", dest="turn_pattern_path", action='store',
                                    help="turn pattern of the simulation.", type=check_file)

    # Retrieve the arguments parsed
    args = arg_parser.parse_args()
    return args


if __name__ == '__main__':

    # Retrieve execution options (parameters)
    exec_options = get_options()

    # Output dir
    output_dir = exec_options.output_directory
    config_dir = output_dir + '/config'

    # Create the directories
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(config_dir).mkdir(parents=True, exist_ok=True)

    # Get number of parent folders to "docker-utils" component:
    num_parent_folders = get_num_parent_folders('docker-utils') * '../'

    # Retrieve topology parameters values
    cols, rows, lanes = int(exec_options.cols), int(exec_options.rows), int(exec_options.lanes)

    # Retrieve traffic time pattern, dates interval and turn pattern
    time_pattern_path = exec_options.time_pattern_path
    dates = exec_options.dates
    turn_pattern_path = exec_options.turn_pattern_path

    # 1. Generate SUMO configuration files and flows with or without turns
    command = f"python {DEFAULT_CONFIG_GENERATOR_SCRIPT} -n {config_dir + '/' + DEFAULT_NODES_FILENAME} " \
              f"-e {config_dir + '/' + DEFAULT_EDGES_FILENAME} -d {config_dir + '/' + DEFAULT_DET_FILENAME} " \
              f"-t {config_dir + '/' + DEFAULT_TLL_FILENAME} -o {config_dir + '/' + DEFAULT_NET_FILENAME} " \
              f"-f {config_dir + '/' + DEFAULT_ROUTE_FILENAME} -s {config_dir + '/' + DEFAULT_CONFIG_FILENAME} " \
              f"-r {rows} -c {cols} -l {lanes} -p --allow-turns "

    if dates:
        command += f"--dates {dates} "
    elif time_pattern_path:
        command += f"--time-pattern {time_pattern_path} "

    if turn_pattern_path:
        command += f"--turn-pattern {turn_pattern_path} "

    # Execute command
    os.system(command)

    # Retrieve OS by parameter
    os_experiment = exec_options.os

    file_extension = '.bat' if os_experiment == 'windows' else '.sh'

    # 2. Create sh file per each adaptation
    for adaptation, tl_components in ADAPTATION_APPROACHES.items():
        # Retrieve file schema, set the adaptation name and initialize the TLC pattern
        file_str, adaptation_name, tlc_pattern = ADAPTATION_FILE_SCHEMA, 'example_' + adaptation, ''

        # Windows
        if os_experiment == "windows":
            # Replace comments, cur directory variable, variable call and file beginning
            file_str = file_str.replace(UBUNTU_START, WINDOWS_START).replace(UBUNTU_ECHO_NULL, WINDOWS_ECHO_NULL) \
                .replace(UBUNTU_COMMENT, WINDOWS_COMMENT).replace(UBUNTU_CUR_DIR, WINDOWS_CUR_DIR) \
                .replace(UBUNTU_VARIABLE, WINDOWS_VARIABLE)
            # Remove "sudo"
            file_str = file_str.replace("sudo ", "")

        # If date interval set pattern parameter
        if dates:
            tlc_pattern = 'date#' + dates
        # If time pattern set pattern parameter
        elif time_pattern_path:
            # Replace ../ for /etc/ -> For Docker-compose
            tlc_pattern = 'pattern#' + time_pattern_path.replace('../', '/etc/')

        # If turns follows a given turn pattern or is not used in the adaptation approach
        if turn_pattern_path and 'no_turn' not in adaptation:
            # Replace ../ for /etc/ -> For Docker-compose generation
            tlc_pattern += ':turn#' + turn_pattern_path.replace('../', '/etc/')
            # If there is a turn pattern load it means the turns are allowed
            tlc_pattern += ':allow-turns#'

        # Define output executable sh file
        file_name = output_dir + '/' + adaptation_name + file_extension

        # Next -> calculate time based on the days selected
        time = 1500

        # Store the file str with the values
        file_str = file_str.format(num_parent_folders=num_parent_folders,
                                   tlc_pattern=tlc_pattern, rows=rows, cols=cols, lanes=lanes,
                                   tl_components=tl_components, add_components='',
                                   exp_file=f'grid_{rows}x{cols}_{adaptation_name}.xlsx', time=str(time),
                                   db_url=';db-host#http://localhost' if os_experiment == 'windows' else '')

        # Change / to \ if os is windows
        if os_experiment == 'windows':
            file_str = file_str.replace(UBUNTU_SLASH, WINDOWS_SLASH)
            num_parent_folders = num_parent_folders.replace(UBUNTU_SLASH, WINDOWS_SLASH)
            tlc_pattern = tlc_pattern.replace(UBUNTU_SLASH, WINDOWS_SLASH)
            tl_components = tl_components.replace(UBUNTU_SLASH, WINDOWS_SLASH)

        # Create each sh file
        with open(file_name, "w") as adaptation_file:
            adaptation_file.write(file_str)

        # Get sh file current permissions
        st = os.stat(file_name)
        # Update the permissions to be executable
        os.chmod(file_name, st.st_mode | stat.S_IEXEC)
