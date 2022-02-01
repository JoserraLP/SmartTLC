#  Traffic Light Study

It is used to perform different studies to select the best traffic light algorithms per each kind of traffic flow, based 
on the total amount of waiting time and the waiting time in each possible direction. The defined temporal window to
store this information is a half hour, which in SUMO is about 1800 timesteps.

Note: this component is not shown in the SmartTLC architecture as it is independent.

There have been defined two different approaches to define the traffic light algorithms:
- **Using time interval of 5 seconds on the green phases**. It results on 11 traffic light algorithms.
- **Using traffic proportion to calculate the green phase**. It results on 5 traffic light algorithms, and it is the one 
  that have been used on the examples.

Besides, it is also have been developed a CLI visualizer tool that allows to create different plots: Box, Scatter, Pair, 
Bar and Line plot.

## Usage
As this component has different generators, there will be described separately:

### Traffic Light Program generator
It generates the XML file in which are stored all the different traffic lights algorithms that will be used on the SUMO
simulation. As there are two different traffic light approaches, there will be two kind of generators, both available on
"config_generator.py".

```sh
# Interval based
python config_generator.py --tl-program-file <tl-program-file> --interval <seconds>

# Proportion based
python config_generator.py --tl-program-file <tl-program-file> --proportion
```

Where the parameters are: 
- **-–tl-program-file** or **-t**: which indicates the output directory where the file is going to be stored. It must 
  have the extension ".ttl.xml".
- **--interval** or **-i**: indicates the interval used to calculate the phases of the different traffic light 
  algorithms. This is the first study approach. 
- **--proportion** or **-p**: that indicates that the traffic lights phases will be calculated based on the traffic 
  flows proportion. This is the second study approach.

Note: both approaches are exclusive, meaning that the options "--interval" and "--proportion" can not be executed at
the same time.

### Eclipse SUMO configuration generator
It generates an XML file following the SUMO configuration file schema in which are indicated values or external files as
the network topology, traffic lights algorithm, GUI settings and additional components as detectors.

```sh
# SUMO simulation config
python config_generator.py --sumo-config-file <sumo-config-file>
# Shorten 
python config_generator.py -s <sumo-config-file>
```

Where the only argument is the output XML file, that must have the extension ".sumocfg".

### Traffic Light Study execution
The traffic light study itself is performed with the next execution commands:
  
```sh
# Interval based
python main.py -c ./net-files/config/simulation.sumocfg -i 5 --nogui -o ../output/simulation_interval_5.csv

# Proportion based
python main.py -c ../net-files/config/simulation.sumocfg -p --nogui -o ../output/simulation_proportion.csv
```

Where the parameters are:
- **--nogui**: flag to use either the SUMO GUI or not in the simulation process. By default, is set to True, 
  which means that the GUI is not used.
- **--config** or **-c**: indicates the location of the SUMO configuration file. By default, is 
  "../net-files/config/simulation.sumocfg". 
- **--cli-visualize**: enables the command line interface visualization developed to create plots about the generated 
  dataset. By default, is disabled. 
- **--interval** or **-i**: indicates the interval used to calculate the phases of the different traffic light 
  algorithms. This is the first study approach. 
- **--proportion** or **-p**: that indicates that the traffic lights phases will be calculated based on the traffic 
  flows proportion. This is the second study approach.
- **--output-file** or **-o**: indicates the directory where the study results will be stored. Default value is 
  “../output/simulation.csv”

## Studies execution
The execution of the two studies it is available on the folder "study", on the project root folder, and there are 
executed with the following commands, respectively:

```sh
# First approach
./study/study_interval_5.sh
# Second approach
./study/study_proportion.sh
```