#!/bin/sh
cd ../traffic_light_study/tl_study && python config_generator.py -t ../net-files/topology/topology.tll.xml -i 5 && python config_generator.py -s ../net-files/config/simulation.sumocfg && python main.py -c ../net-files/config/simulation.sumocfg -i 5 --nogui -o ../output/simulation_interval_5.csv && python main.py --cli-visualize
