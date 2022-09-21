# Traffic Analyzer

It analyzes the number of passing vehicles in each possible direction, and selects the traffic type that fits better the
current situation. It is important to mention that it analyzes the traffic of single traffic light individually.


In order to analyze those traffic values, there have been defined several bounds, related directly to the different 
traffic types passing per each direction.
- **Lower bound**: it is the upper bound of the previous type, except for the lowest type that is 0.
- **Upper bound**: it is calculated by adding the number of vehicles per hour and the maximum possible value in its range, 
  and dividing this sum by proportion value based on the temporal window selected. 

## Usage

This component is executed with the following command:
```sh
python main.py <parameters>
```

Where the parameters defined are:

- **-h, --help**: show this help message and exit.
- **-t TEMPORAL_WINDOW, --temporal-window TEMPORAL_WINDOW**: define the traffic monitoring temporal window. 
  Default is *5*.
- **--middleware_host MQTT_URL**: middleware broker host. Default is *172.20.0.2*.
- **--middleware_port MQTT_PORT**: middleware broker port. Default is *1883*.

## Data model
The followed schema to publish the analyzed information into the middleware is:
- **traffic_analysis**: traffic flow type analysis previously defined. It represents only one type of traffic flow. 
  Possible values are from 0 to 11.
  
Besides, the topic used to publish this information is "traffic_analysis/<traffic_light_id>", where the 
*<traffic_light_id>* is the traffic light identifier. 
