#! /bin/bash

# Start server in docker container, from image hosted on the multi-user gitlab's container registry
docker run -d \
    -p 5555-5560:5555-5560 \
    -e port=5555 \
    -e log-level DEBUG \
    -e password=admin \
    -e timeout=1000 \
    registry.gitlab.com/slumber/multi-user/multi-user-server:0.1.0