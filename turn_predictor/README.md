#  Turn Predictor

This component is based on several *Machine Learning* algorithms that will learn the vehicles turn probabilities in all
directions (left, right and forward) at a given road and a given moment.

These regression algorithms are: (1) Linear Regression; (2) K-Nearest Neighbors; (3) Decision Trees; and 
(4) Random Forest.
  
## Dataset data model
The followed schema is used to store the information into the training dataset:
- **date_year**: number representing the year. 
- **date_month**: number representing the month, where the minimum and maximum possible values are 1 and 12, 
respectively.
- **date_day**: number representing the day, where the minimum and maximum possible values are 1 and 31, respectively. 
  Note that there are months, as February, where the maximum value is 28.
- **hour**: it represents the current hour of the simulation. This information is stored by default each half-hour, 
  which in the simulator is a total of 1.800 timesteps.
- **turn_right**: probability of turning to right of a road. Its value is in range [0.0, 1.0]. Default to *0.20*.
- **turn_left**: probability of turning to left of a road. Its value is in range [0.0, 1.0]. Default to *0.20*.
- **turn_forward**: probability of keep forward (not turning). Its value is in range [0.0, 1.0]. Default to *0.60*.
- **road**: a road name. It is possible to specify "all" if the probabilities defined are the same for all the roads, 
  otherwise, specify those specific probabilities. In this case, those unspecified roads will use the default values.
  
Note: all the turn probabilities must add up to 1.0, not higher nor lower. Besides, it is possible to specify different
probabilities per each road, splitting by ';' character on the fields: turn_right, turn_left, turn_forward and road.

## Usage
In this component, there are several scripts:

### Machine Learning processes
Both training and prediction processes are executed with the script "ml_trainer.py".

-  **-h, --help**: show this help message and exit.

#### Training
It performs the training process of each ML model. Its parameters are:

- **-t INPUT_FILE, --train INPUT_FILE**: starts the training process and indicates the input dataset file used to train 
  the models. 
- **--rows ROWS**: network topology matrix number of rows.
- **--cols COLS**: network topology matrix number of columns.
- **-f FOLDS, --folds FOLDS**: k-fold number of folds. Default is *2*.
- **-c, --clean**: it deletes the models stored previously if enabled. By default, By default, is *False*, 
  meaning it is disabled.

```sh 
python ml_trainer.py --train .../../sumo-utils/time_patterns/turn_patterns/turn_week_route_equal_time.csv -c --cols 3 
--rows 3
```

#### Prediction
It performs the prediction process with the best ML model. Its only parameter is **--predict** or **-p** to predict the 
traffic type from the indicated input, split by a comma. Default format is: "road, hour, date_day, date_month, date_year".

```sh 
python ml_trainer.py --predict c2_c1,0:00,2,1,2021
```

### Full component
Even the deployment of the full component is executed with the "ml_trainer.py" script. Its parameters are: 
- **--component**: flag to deploy the full component with the trained models. By default, is enabled. 
- **-n NUM_MODELS, --num-models NUM_MODELS**: number of models used to make the traffic type prediction, now only works 
  with one predictor. By default, is *1*. 
- **--middleware_host MQTT_URL**: indicates the middleware broker url. By default, is *172.20.0.2* 
- **--middleware_port MQTT_PORT**: indicates the middleware broker port. By default, it is *1883*.

```sh 
python ml_trainer.py --component -n 1
```

## Data model
The data model consists on a dictionary where the key is the name of the road, and its value is, respectively:
- **turn_prob_right**: probability of turning right on the road.
- **turn_prob_left**: probability of turning left on the road.
- **turn_prob_forward**: probability of going forward on the road.  

Besides, the topic used to publish this information is "turn_prediction/<traffic_light_id>", where the 
*<traffic_light_id>* is the traffic light identifier. 



