#!/bin/sh

# Move to traffic light study folder
cd ../traffic_light_study/tl_study || exit

# Generate the Traffic Light programs by interval of 5 seconds
python config_generator.py -t ../net-files/topology/topology.tll.xml -i 5 

# Generate the SUMO configuration file
python config_generator.py -s ../net-files/config/simulation.sumocfg 

# Execute the SUMO simulation
python main.py -c ../net-files/config/simulation.sumocfg -i 5 --nogui -o ../output/simulation_interval_5.csv 

# Execute the CLI visualizer
python main.py --cli-visualize
