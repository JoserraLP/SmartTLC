#  Traffic Predictor
This component is based on several *Machine Learning* algorithms that will learn to identify the different traffic types
based on information about predefined time patterns. It is important to mention that it analyzes the traffic of single 
traffic light individually.


These algorithms are: (1) Naive Gaussian Bayes; (2) Support Vector Machines both linear and polynomial; (3) K-Nearest 
Neighbors; (4) Decision Trees; and (5) Random Forest.

## Dataset Generator
The generator itself is based on both predefined time patterns, and a noise policy in order to represent the uncertainty
of the traffic. Besides, it is worth mentioning that it is based on a working calendar from 2019 to 2023 of Extremadura
and Andalucia where are defined several the bank holidays and working days of each year.

### Noise policy
This policy is described as follows:
- **Day replacement**: there are main considerations:
  - Swap once every 50 working days with a bank holiday or weekend day
  - Swap once every 20 weekend days with a working day
- **Traffic type replacement**: one hour every three days (72 hours), modify the traffic type by adding or 
  subtracting a random value with a range of plus or minus one.
  
### Dataset data model
The followed schema is used to store the information into the dataset:
- **hour**: slice representing each hour of a day
- **traffic_type**: related traffic type. It has to be one of the valid traffic types
- **day**: day name. Its possible values are: monday, tuesday, wednesday, thursday, friday, saturday and sunday.
- **date_day**: number representing the day. Higher value can be 31 and must be greater than 0
- **date_month**: number representing the month. Higher value can be 12 and must be greater than 0
- **date_year**: number representing the year.
  
## Usage
In this component, there are several scripts:

### Traffic time pattern calendar dataset file generator
In order to generate the calendar dataset, the following script must be executed.
```sh
python dataset_generator.py -i ../../sumo-utils/time_patterns/working_calendars/working_calendar_andalucia.csv
```

Where the parameters are:
- **-h, --help**: show this help message and exit
- **-i INPUT_CALENDAR, --input-calendar INPUT_CALENDAR**: input working calendar file. Mandatory
- **-o OUTPUT_FILE, --output-file OUTPUT_FILE**: output traffic time pattern file. 
  Default to ../../sumo-utils/time_patterns/calendar_time_pattern.csv


### Machine Learning processes
Both training and prediction processes are executed with the script "ml_trainer.py".

#### Training
It performs the training process of each ML model. Its parameters are: 
- **-i INPUT_FILE, --input-file INPUT_FILE**: starts the training process and indicates the input dataset file used to train
  the models. 
- **-f FOLDS, --folds FOLDS**: k-fold split dataset process number of folds. Default is *2*.
- **-c, --clean**: it deletes the models stored previously if enabled. By default, By default, is *False*, meaning it 
  is disabled.

```sh 
python ml_trainer.py --input-file ../../sumo-utils/time_patterns/calendar_time_pattern.csv -c
```

#### Prediction
It performs the prediction process with the best ML model. Its only parameter is **--predict** or **-p** to predict the 
traffic type from the indicated input, split by a comma. Default format is "hour, day, date_day, date_month, date_year". 

```sh 
python ml_trainer.py --predict 10:30,monday,01,02,2021
```

### Full component
Even the deployment of the full component is executed with the "ml_trainer.py" script. Its parameters are: 
- **--component**: flag to deploy the full component with the trained models. By default, is *True*, meaning that is 
  enabled. 
- **-n NUM_MODELS, --num-models NUM_MODELS**: number of models used to make the traffic type prediction, now only works 
  with one predictor. By default, is *1*. 
- **--middleware_host MQTT_URL**: indicates the middleware broker URL. By default, is *172.20.0.2* 
- **--middleware_port MQTT_PORT**: indicates the middleware broker port. By default, it is *1883*.

```sh 
python ml_trainer.py --component -n 1
```

## Data model
The followed schema to publish the predicted information into the middleware is a dictionary with the following info:
- **lane name**: as the key.
- **predicted traffic type**: as the value where it can be on the interval [0, 4], representing all possible traffic 
types currently.
  
Besides, the topic used to publish this information is "traffic_prediction/<traffic_light_id>", where the 
*<traffic_light_id>* is the traffic light identifier that is connected to the given lane. 

