#!/bin/sh
cd ../traffic_light_study/tl_study && python config_generator.py -t ../net-files/topology/topology.tll.xml -p && python config_generator.py -s ../net-files/config/simulation.sumocfg && python main.py -c ../net-files/config/simulation.sumocfg --nogui -o ../output/simulation_proportion.csv && python main.py --cli-visualize
