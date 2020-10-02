# Download base image debian jessie
FROM python:slim

# Infos
LABEL maintainer="Swann Martinez"
LABEL version="0.1.0"
LABEL description="Blender multi-user addon  \
    dedicated server image."

ARG version=0.0.21a15

# Argument
ENV password='admin'
ENV port=5555
ENV timeout=3000
ENV log_level=INFO
ENV log_file="multiuser_server.log"

#Install replication
RUN pip install replication==$version

# Run the server with parameters
CMD  replication.serve -pwd ${password} -p ${port} -t ${timeout} -l ${log_level} -lf ${log_file}
