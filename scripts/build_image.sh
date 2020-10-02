#!/bin/bash

VERSION="$(python get_replication_version.py)"

echo "Building docker image with version ${VERSION}"
docker build --no-cache --build-arg version=${VERSION} -t registry.gitlab.com/slumber/multi-user/multi-user-server:0.1.0 ./docker_server

echo "Pushing to gitlab registry ${VERSION}"
docker push registry.gitlab.com/slumber/multi-user/multi-user-server:0.1.0 