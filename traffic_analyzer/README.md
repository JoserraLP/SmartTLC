# Traffic Analyzer

It analyzes the number of passing vehicles on a single lane, and selects the traffic type that fits better the
current situation. In order to analyze those traffic values, there have been defined several bounds, related directly to the different 
traffic types passing on the lane, based directly on the lower and upper bound of the defined traffic types, 
divided by the proportion value based on the temporal window selected.

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
The followed schema to publish the analyzed information into the middleware is a dictionary with the following info:
- **lane name**: as the key.
- **analyzed traffic type**: as the value where it can be on the interval [0, 4], representing all possible traffic 
types currently.  
  
Besides, the topic used to publish this information is "traffic_analysis/<traffic_light_id>", where the 
*<traffic_light_id>* is the traffic light identifier that is connected to the given lane. 
