# Download base image debian jessie
FROM python:slim

ARG replication_version=0.9.1
ARG version=0.1.1

# Infos
LABEL maintainer="Swann Martinez"
LABEL version=$version
LABEL description="Blender multi-user addon  \
    dedicated server image."

# Argument
ENV password='admin'
ENV port=5555
ENV timeout=5000
ENV log_level=DEBUG
ENV log_file="multiuser_server.log"

#Install replication
RUN pip install replication==$replication_version

# Run the server with parameters
ENTRYPOINT ["/bin/sh", "-c"]
CMD  ["python3 -m replication.server -apwd ${password} -p ${port} -t ${timeout} -l ${log_level} -lf ${log_file}"]