# Experiment collector
Script for retrieving all the information related to a given experiment from the *data storage* component.

## Usage
The execution itself is performed by executing the next command

```sh
python main.py <parameters>
```

This execution process creates a file where there is stored all the traffic information related to an experiment.

Where the parameters defined are:

- **-h, --help**: show this help message and exit.
- **-o OUTPUT_FILE, --output-file OUTPUT_FILE**: define the output file location. Must be an XLSX file. 
  Default is *./data.xlsx*.
- **-w WAITING_TIME, --waiting-time WAITING_TIME**: waiting seconds to deploy. Use only when deploying Docker container 
  because the experiment lasts several minutes being executed. Default to *0*, meaning that it deploys instantly.
  
## Data model
The information stored in the output file uses the following model:
- **date_day**: integer number representing the day.
- **date_month**: integer number representing the month.
- **date_year**: integer number representing the year.
- **hours**: it represents the current hour of the simulation. It stores information based on the defined temporal 
  window of 5 minutes.
- **passing_veh_e_w**: number of vehicles that have passed from both east and west.
- **passing_veh_n_s**: number of vehicles that have passed from both north and south.
- **waiting_time_veh_e_w**: amount of time the vehicles that have passed from both east and west.
- **waiting_time_veh_n_s**: amount of time the vehicles that have passed from both north and south.
- **junction**: junction identifier.
- **average**: average value of waiting time per vehicle in all the junctions.
