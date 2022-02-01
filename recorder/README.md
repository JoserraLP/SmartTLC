# Recorder component
This component is related to the record of a given experiment. 

It stores all the information from the topics specified by parameters, along with the timestamp where the data have 
been stored. 

## Execution
The execution command for this component is the following one:

```sh
# Example recording the traffic_light_controller component (topic = 'traffic_info')
python main.py --broker-url <broker-url> --broker-port <broker-port> --topics traffic_info --output-file <experiment-file>
```

Where the parameters are:
- **--output-file** or **-o**: indicates the output file where it is stored the experiment. By default, it is 
  record_[current_date].csv
- **--topics** or **-t**: indicates the topics that will be subscribed to, in order to store all its information from the 
  middleware. By default, it records all the topics ("#").
- **-–broker-url** or **-b**: indicates the middleware broker url. By default, it is "172.20.0.2". 
- **--broker-port** or **-p**: indicates the middleware broker port. By default, it is "1883".
