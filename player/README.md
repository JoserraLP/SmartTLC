# Player component
This component is related to the reproduction of a previously recorded experiment. 

It publishes the information recorded being aware of the time difference between data, replacing the component(s) that
have been recorded on a previous experiment.

## Execution
The execution command for this component is the following one:

```sh
# Example reproducing the traffic_light_controller component (topic = 'traffic_info')
python main.py --broker-url <broker-url> --broker-port <broker-port> --topics traffic_info --input-file <experiment-file>
```

Where the parameters are:
- **--input-file** or **-i**: indicates the input file from where it is retrieved the experiment data.
- **--topics** or **-t**: indicates the topics that will be subscribed to, in order to store all its information from the 
  middleware. By default, it records all the topics ("#").
- **-–broker-url** or **-b**: indicates the middleware broker url. By default, it is "172.20.0.2". 
- **--broker-port** or **-p**: indicates the middleware broker port. By default, it is "1883".