# Multi-User Blender Internet Server

Deploy this server to enable real-time Blender collaboration over the internet.

## Quick Start

### Option 1: Docker Deployment (Recommended)

1. **Prepare the server directory**:
   ```bash
   # The replication wheel should already be in the server directory
   # If not, copy it:
   cd multi-user/server
   cp ../multi_user/wheels/replication-0.9.10-py3-none-any.whl .
   ```

2. **Copy the server directory to your cloud server**:
   ```bash
   scp -r server/ user@your-server.com:~/blender-server/
   ```

3. **SSH into your server**:
   ```bash
   ssh user@your-server.com
   cd ~/blender-server
   ```

4. **Configure your passwords**:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your passwords
   ```

5. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

6. **Check server status**:
   ```bash
   docker-compose logs -f
   ```

### Option 2: Python Deployment

1. **Install Python 3.11+** on your server

2. **Copy the entire multi-user directory** to your server:
   ```bash
   scp -r multi-user/ user@your-server.com:~/
   ```

3. **Install dependencies**:
   ```bash
   cd ~/multi-user/server
   pip install -r requirements.txt
   pip install ../multi_user/wheels/replication-0.9.10-py3-none-any.whl
   ```

4. **Run the server**:
   ```bash
   python -m replication.server \
     --port 5555 \
     --admin-password YOUR_ADMIN_PASSWORD \
     --server-password YOUR_SERVER_PASSWORD \
     --log-level INFO
   ```

## Server Configuration

### Ports

The server uses **3 consecutive ports**:
- **Base Port (default 5555)**: Command channel
- **Base Port + 1 (5556)**: Data replication channel
- **Base Port + 2 (5557)**: Heartbeat/TTL channel

**Firewall Configuration**:
```bash
# Allow the three ports
sudo ufw allow 5555/tcp
sudo ufw allow 5556/tcp
sudo ufw allow 5557/tcp
```

### Environment Variables

Edit [.env](.env.example) to configure:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ADMIN_PASSWORD` | Admin password for kicking users, etc. | `admin` | Yes |
| `SERVER_PASSWORD` | Password clients need to connect (empty = public) | (empty) | No |
| `PORT` | Base port number | `5555` | No |
| `LOG_LEVEL` | Logging verbosity (DEBUG/INFO/WARNING/ERROR) | `INFO` | No |
| `TIMEOUT` | Connection timeout in milliseconds | `10000` | No |

### Security Best Practices

1. **Always set a strong admin password**:
   ```bash
   ADMIN_PASSWORD=$(openssl rand -base64 32)
   ```

2. **For private servers, set a server password**:
   ```bash
   SERVER_PASSWORD=$(openssl rand -base64 24)
   ```

3. **Use a firewall** to restrict access if needed

4. **Consider using a reverse proxy** with SSL/TLS:
   - Nginx or Caddy can provide HTTPS
   - Use WebSocket tunneling for encrypted connections

## Client Configuration

### In Blender

1. Open Blender with the Multi-User addon installed

2. Go to **Edit → Preferences → Add-ons → Multi-User**

3. Find the "Internet Server (Configure Me)" preset

4. Edit the preset:
   - **Server Name**: Give it a descriptive name
   - **IP**: Your server's public IP or domain name
   - **Port**: 5555 (or your custom port)
   - **Admin Password**: The password you set
   - **Server Password**: The password you set (if any)

5. Click **Join Session** to connect

## Server Management

### Docker Commands

```bash
# View logs
docker-compose logs -f

# Stop server
docker-compose down

# Restart server
docker-compose restart

# Update and rebuild
docker-compose down
docker-compose build
docker-compose up -d
```

### Server Shell Commands

When running the server (non-Docker), you get an interactive shell:

```
>> help          # Show available commands
>> users         # List connected users
>> kick <user>   # Kick a user
>> exit          # Stop the server
```

### Monitoring

Check connection status:
```bash
# Watch for new connections
tail -f multi_user_server.log | grep "Auth request"

# Monitor active users
tail -f multi_user_server.log | grep "user online"
```

## Troubleshooting

### Cannot connect from client

1. **Check firewall**:
   ```bash
   # On server
   sudo ufw status
   ```

2. **Verify server is listening**:
   ```bash
   netstat -tuln | grep 5555
   ```

3. **Test connectivity**:
   ```bash
   # From client machine
   telnet your-server.com 5555
   ```

4. **Check server logs**:
   ```bash
   docker-compose logs | tail -50
   ```

### Connection timeout

- Increase `TIMEOUT` in .env
- Check network latency: `ping your-server.com`
- Verify all 3 ports (5555, 5556, 5557) are accessible

### Password authentication fails

- Ensure passwords match exactly (no trailing spaces)
- Check if server password is required: `use_server_password=True`
- Verify admin password if trying admin operations

## Performance Tuning

### For high-latency connections:

```bash
# Increase timeout to 30 seconds
TIMEOUT=30000
```

### For many simultaneous users:

1. Increase system limits:
   ```bash
   # /etc/security/limits.conf
   * soft nofile 65536
   * hard nofile 65536
   ```

2. Monitor memory usage:
   ```bash
   docker stats blender-multiuser-server
   ```

## Advanced: SSL/TLS Encryption

The replication protocol uses plain TCP. For encrypted connections, use a reverse proxy:

### Nginx Example:

```nginx
stream {
    upstream blender_command {
        server 127.0.0.1:5555;
    }

    server {
        listen 443 ssl;
        proxy_pass blender_command;

        ssl_certificate /path/to/cert.pem;
        ssl_certificate_key /path/to/key.pem;
    }
}
```

Then clients connect to port 443 with SSL enabled.

## Cloud Provider Examples

### AWS EC2

1. Launch Ubuntu 22.04 instance (t3.medium or larger)
2. Configure Security Group to allow ports 5555-5557
3. Associate Elastic IP for stable address
4. Follow Docker deployment steps

### DigitalOcean Droplet

1. Create Ubuntu 22.04 droplet ($12/month recommended)
2. Configure firewall in Cloud Panel
3. Use droplet IP or add custom domain
4. Follow Docker deployment steps

### Azure VM

1. Create Ubuntu 22.04 VM (Standard B2s or larger)
2. Configure Network Security Group rules
3. Assign static public IP
4. Follow Docker deployment steps

## Support

For issues with the server deployment:
- Check server logs: `docker-compose logs`
- Verify network connectivity
- Ensure all ports are accessible
- Review Blender addon logs in Blender's System Console

For issues with the Multi-User addon:
- Visit: https://github.com/GPLv3/multi-user (or the original repo)
- Check Blender's System Console for error messages

## Architecture

```
Internet
    │
    ├─── Client A (Home) ──┐
    │                      │
    ├─── Client B (Office) ├──► Cloud Server ──► ZMQ Server
    │                      │    (Ports 5555-5557)
    └─── Client C (Remote) ┘
```

The server acts as a central hub, routing all updates between clients in real-time using ZeroMQ message passing and delta-based synchronization.
