#  Traffic Predictor
This component is based on several *Machine Learning* algorithms that will learn to identify the different traffic types
based on information about predefined time patterns.

These algorithms are: (1) Naive Gaussian Bayes; (2) Support Vector Machines both linear and polynomial; (3) K-Nearest 
Neighbors; (4) Decision Trees; and (5) Random Forest.

## Dataset Generator
The generator itself is based on both predefined time patterns and a noise policy in order to make the dataset more 
realistic. Besides, it is worth mentioning that it is based on a 2021 Madrid's city calendar, where are defined several
bank holidays and working days.

### Noise policy
This policy is described as follows:
- **Day replacement**: there are main considerations:
  - If the date is not a vacation day, meaning that are only considered working days and bank holidays:
    - Once every 50 days, replace the date with a summer or winter vacation day. 
    - Once each 14 working days, swap it with another random working day. This swapping process does not affect bank 
      holidays. 
  - If the date is a vacation day, there are two considerations: 
    - Once every fifteen days, swap the vacation day to a working day. 
    - If the day is summer let it as predefined or swap it to a winter vacation day, once per every fifteen days. 
    - If the day is winter let it as predefined or swap it to a summer vacation day, once per every fifteen days.
- **Traffic type replacement**: once every three days, modify a traffic type flow of a given slice by adding or 
  subtracting a random value with a range of plus or minus two.
  
### Dataset data model
The followed schema is used to store the information into the dataset:
- **sim_id**: SUMO simulation identifier. It is stored as a key of the different rows of information but it is not used 
  at all.
- **tl_id**: junction identifier that in this case, as there is only one junction, will have always the same value "c1".
- **tl_program**: traffic light algorithm used in the simulation. This field is always "static" as it is used in real 
  life.
- **traffic_type**: traffic flow type representing all its possible values, from 0 to 11. This field is the one that 
  will be predicted by the TLP component.
- **passing_veh_n_s**: number of vehicles that have passed from both north and south. It must be greater than 0.
- **passing_veh_e_w**: number of vehicles that have passed from both east and west. It must be greater than 0.
- **hour**: it represents the current hour of the simulation. This information is stored by default each half-hour, 
  which in the simulator is a total of 1.800 timesteps.
- **day**: it represents the name of the day it is currently on the simulation. Note that one day in the simulator is 
  represented with a total of 86.400 timesteps, and its value is retrieved from Madrid’s calendar. 
  All the possible values are Monday, Tuesday, Wednesday, Thursday, Friday, Saturday and Sunday.
- **date_day**: number representing the day, where the minimum and maximum possible values are 1 and 31, respectively. 
  Note that there are months, as February, where the maximum value is 28.
- **date_month**: number representing the month, where the minimum and maximum possible values are 1 and 12, 
  respectively.
- **date_year**: number representing the year. In this case, the only possible value is 2021 as it is the simulated 
  year.
  
## Usage
In this component, there are several scripts:

### Dataset generator
Firstly, it is required to generate the calendar with the time patterns and noise policy. The "config_generator" 
parses and creates a “.csv” file where it is stored the calendar that will be used to generate the simulation 
dataset. In the generated calendar, there is used the noise policy and the different hand-made time patterns to 
generate the calendar based on an existing calendar with bank holidays and working days.

In order to execute this generator, execute the following command:

```sh
python config_generator.py --calendar ../time_patterns/calendar.csv
```

Where the only parameter is the **--calendar** or **-c**, which indicates the input calendar file. The output simulation 
calendar is stored by default in "../time_patterns/generated_calendar.csv".

Once the calendar have been generated, it is generated the dataset related to it, with the script "dataset_generator.py",
where it is possible to use two approaches: with a number of simulations per traffic algorithm and with a given time 
pattern. This last one is the used to generate the TLP training dataset.
```sh
# Time pattern
python dataset_generator.py --time-pattern ../time_patterns/generated_calendar.csv -c \
../net-files/config/simulation.sumocfg -o ../output/simulation_calendar.csv --nogui

# Number of simulations
python dataset_generator.py --num-sim 2 -c ../net-files/config/simulation.sumocfg -o \
../output/simulation_calendar.csv --nogui

# CLI visualizer tool
python dataset_generator.py --cli-visualize
```

Where the parameters are:
- **--num-sim** or **-n**: indicates the number of simulations that will be performed to generate the dataset. 
  By default is 0. This parameter can not be used with the next one.
- **--time-pattern** or **-t**: indicates the directory where the time pattern, that will be used to generate the 
  dataset, is stored.
- **--output-file** or **-o**: indicates the directory where the generated dataset will be stored. By default is 
  “../output/simulation calendar.csv”.
- **--cli-visualize**: enables the command line interface visualization developed to create plots about the generated 
  dataset. By default is disabled.

### Machine Learning processes
Both training and prediction processes are executed with the script "ml_trainer.py".

It is worth mentioning that there is a global parameter that enables the date-based predictors, which is by default 
disabled, which means that the TLP will use context-based predictors by default. This parameter is **--date** or **-d**.

#### Training
It performs the training process of each ML model. Its parameters are: 
- **--train** or **-t**: starts the training process and  indicates the input dataset file used to train the models. 
- **--clean** or **-c**: it deletes the models stored previously if enabled. By default is disabled.

```sh 
python ml_trainer.py --train ../output/simulation_calendar.csv -c
```

#### Prediction
It performs the prediction process with the best ML model. Its only parameter is **--predict** or **-p** to predict the 
traffic type from the indicated input, split by comma. Default format is: "passing_veh_e_w, passing_veh_n_s, hour, day, 
date_day, date_month, date_year". If "date" flag is active, the fields are: "hour, day, date_day, date_month, date_year". 

```sh 
python ml_trainer.py --predict 10,10,10:30,Monday,01,02,2021
```

### Full component
Even the deployment of the full component is executed with the "ml_trainer.py" script. Its parameters are: 
- **--component**: flag to deploy the full component with the trained models. By default is enabled. 
- **--num-models** or **-n**: number of models used to make the traffic type prediction, now only works with one predictor. 
  By default is 1. 
- **--middleware_host**: indicates the middleware broker url. By default is 172.20.0.2 
- **--middleware_port**: indicates the middleware broker port. By default it is 1883.

```sh 
python ml_trainer.py --component -n 1
```

## Data model
The followed schema to publish the analyzed information into the middleware is:
- **tl_id**: traffic light identifier. In this case, it will only be "c1" as there is only one
traffic light in the scenario. 
- **traffic_prediction**: traffic flow type prediction. It represents only one type of traffic flow type. 
  The possible values are from 0 to 11.
  
Besides, the topic used to publish this information is "traffic_prediction". 



