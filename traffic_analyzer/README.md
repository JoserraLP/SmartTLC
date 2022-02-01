# Traffic Analyzer

It analyzes the number of passing vehicles in each possible direction, and selects the traffic type that fits better the
current situation. 


In order to analyze those traffic values, there have been defined several bounds, related directly to the different 
traffic types passing per each direction.
- Lower bound: it is the upper bound of the previous type, except for the lowest type that is 0.
- Upper bound: it is calculated by adding the number of vehicles per hour and the maximum possible value in its range, 
  and dividing this sum by three (selected manually). 

## Usage

This component does not have any execution parameters, and it is executed with the following command:
```sh
python main.py
```

## Data model
The followed schema to publish the analyzed information into the middleware is:
- **tl_id**: traffic light identifier. In this case, it will only be "c1" as there is only one
traffic light in the scenario.
- **traffic_analysis**: traffic flow type analysis previously defined. It represents only
one type of traffic flow. The possible values are from 0 to 11.
  
Besides, the topic used to publish this information is "traffic_analysis". 
