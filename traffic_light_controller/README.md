#  Traffic Light Controller
It is the component that will simulate the traffic time patterns and perform the traffic light adaptation based on the
Traffic Light Adapter sub-component (described below). The default behavior of the traffic light algorithms is an 
equally distributed algorithm with 40 seconds of green phase and 5 seconds on amber phase per direction. 

This component retrieve contextual information (waiting time and number of vehicles passing per direction) from the 
traffic simulation each 30 minutes.  

## Usage
The execution command for this component is the following one:
```sh
# Simulation with dates from 01/01/2021 to 02/01/2021 
python main.py --nogui --dates 01/01/2021-02/01/2021

# Simulation with a given time pattern (Monday)
python main.py --nogui --time-pattern ../time_patterns/base_patterns/monday.csv
```

Where the parameters are:
- **--nogui**: flag to use either the SUMO GUI or not in the simulation process. By default, is set to True, which means 
  that the GUI is not used.
- **-–config** or **-c**: indicates the location of the SUMO configuration file. By default, is 
  “../net-files/config/simulation.sumocfg”. 
- **-–time-pattern** or **-t**: indicates the file where the input time pattern is located. It can not be used along 
  with the next parameter. 
- **--dates** or **-d**: indicates the range of dates, retrieved from the generated calendar, that will be simulated. 
  The format is dd/mm/yyyy-dd/mm/yyyy, where the first date is the start, and the second one is the end, both included.
  
Note that the time pattern and dates are indicated in the deployment scripts with the characters ":" and "#".

Besides, the configuration scripts explained on the "Traffic Light Study" components are used in this component too.

## Data model
The followed schema to publish the analyzed information into the middleware is:
- **tl_id**: junction identifier that in this case, as there is only one junction, will have always the same value “c1”. 
- **tl_program**: traffic light algorithm used in the simulation. 
- **passing_veh_n_s**: number of vehicles that have passed from both north and south. It must be greater than 0.
- **passing_veh_e_w**: number of vehicles that have passed from both east and west. It must be greater than 0.
- **waiting_time_veh_n_s**: amount of time the vehicles that have passed from both north and south have 
  been waiting in total. It must be greater than 0.
- **waiting_time_veh_e_w**: amount of time the vehicles that have passed from both east and west. 
  It must be greater than 0.
- **hour**: it represents the current hour of the simulation. It only allows values that are half hours.
- **day**: it represents the name of the day it is currently on the simulation. By default, is Monday.
- **date_day**: integer number representing the day, where the minimum and maximum possible values are 1 and 31, 
  respectively. By default, is 2.
- **date_month**: integer number representing the month, where the minimum and maximum possible values are 1 and 12, 
  respectively. By default, is 2.
- **date_year**: integer number representing the year. In this case, the default value is "2021".

Besides, the topic used to publish this information is "traffic_info". 

#  Traffic Light Adapter
This component is related to the adaptation process of the traffic light algorithms based on the traffic type selected 
and predicted from the Traffic Analyzer and Traffic Light Predictor, respectively.

The main considerations about this component are:
- If there is only one traffic type related component (TA or TLP) deployed, the traffic type used to select the best 
  traffic light algorithm will be the one retrieved by that component as the other one is down and does not provide any 
  kind of information.
- If there is information about the two components:
  - If the prediction and the analyzed traffic type are very close, within a minimum predefined “distance”, 
  the analyzed traffic type will be the one that will be used to adapt the traffic light algorithm. By default, the 
  value of this “distance” is three. 
  - Otherwise, the value used to adapt the traffic light is calculated by the third part of the distance between the 
  analyzed and the predicted traffic types, getting closer to the analyzer value.