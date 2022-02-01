# Recorder component
This component is related to the record of a given experiment. 

It stores all the information from the topics specified by parameters, along with the timestamp where the data have 
been stored. 

## Execution
The execution command for this component is the following one:

```sh
# Example recording the traffic_light_controller component (topic = 'traffic_info')
python main.py --broker-url <broker-url> --broker-port <broker-port> --topics traffic_info --output-file <experiment-file>

# Or shorten 
python main.py -b <broker-url> -p <broker-port> -t traffic_info -o <experiment-file>
```

Where default values are:
- **broker-url**: 172.20.0.2
- **broker-port**: 1883
- **topics**: all the topics (#)
- **output-file**: record_[current_date].csv