FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install the replication wheel
COPY replication-0.9.10-py3-none-any.whl .
RUN pip install --no-cache-dir replication-0.9.10-py3-none-any.whl

# Copy server scripts
COPY standalone_server.py .
COPY persistent_server.py .

# Expose ports (command: 5555, data: 5556, ttl: 5557)
EXPOSE 5555 5556 5557

# Environment variables for configuration
ENV PORT=5555
ENV ADMIN_PASSWORD=admin
ENV SERVER_PASSWORD=""
ENV LOG_LEVEL=INFO
ENV TIMEOUT=10000
ENV DATA_DIR=/app/data
ENV SAVE_INTERVAL=120
ENV MAX_BACKUPS=10

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import zmq; ctx = zmq.Context(); s = ctx.socket(zmq.REQ); s.connect('tcp://localhost:${PORT}'); s.close()" || exit 1

# Create data directory
RUN mkdir -p /app/data

# Run the persistent server (with auto-save)
CMD python persistent_server.py \
    --port ${PORT} \
    --admin-password ${ADMIN_PASSWORD} \
    --server-password ${SERVER_PASSWORD} \
    --log-level ${LOG_LEVEL} \
    --timeout ${TIMEOUT}
