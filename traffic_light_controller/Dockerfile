FROM ubuntu:18.04

# -----> ADD REQUIRED LIBS

RUN apt-get update && apt-get install -y git cmake python3.8 python3-pip g++ libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev libgl2ps-dev

# -----> INSTALL SUMO
RUN apt-get install -y sumo sumo-tools sumo-doc

# -----> DOWNLOAD SUMO, EXPORT SUMO_HOME AND COMPILE IT
RUN git clone --recursive https://github.com/eclipse/sumo
RUN export SUMO_HOME="/sumo/" 
RUN mkdir /sumo/build/cmake-build && cd /sumo/build/cmake-build && cmake ../.. && make

# -----> ADD DOCKERIZE TOOL

RUN apt-get update && apt-get install -y wget

ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz
