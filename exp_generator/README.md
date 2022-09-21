# Experiment generator
Script for generating an experiment based on the information provided by parameters. The output is a folder that 
contains each one of the available adaptation approaches, and the vehicle flows file related.

## Usage
The execution itself is performed by executing the next command

```sh
python main.py <parameters>
```

Where the parameters defined are:

- **-h, --help**: show this help message and exit
- **-o OUTPUT_DIRECTORY, --output-dir OUTPUT_DIRECTORY**: output directory location.
- **Network topology parameters**:
  - **-c COLS, --columns COLS**: grid topology columns. Must be greater than 1.
  - **-r ROWS, --rows ROWS**: grid topology rows. Must be greater than 1.
  - **-l LANES, --lanes LANES**: grid topology lanes. Must be greater than 1.
- **Time pattern parameters**: One of the parameters must be set.
  - **-t TIME_PATTERN_PATH, --time-pattern TIME_PATTERN_PATH**: time pattern to load the flows.
  - **-d DATES, --dates DATES**: calendar dates from start to end to simulate. Format is **dd/mm/yyyy-dd/mm/yyyy**.
- **Turn pattern parameters**: It is optional.
  - **--turn-pattern TURN_PATTERN_PATH**: turn pattern of the simulation.
  
Note: in the script itself, all the parameters are grouped based on its functionality, but in this case
it is not shown here in order to clarify its reading. If you want to see these groups execute the script 
with the **-h** or **--help** argument.