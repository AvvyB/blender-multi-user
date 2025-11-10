# Quick Reference Card

## Server Deployment (One-time Setup)

### Docker (Recommended)
```bash
cd server/
cp .env.example .env
nano .env  # Set ADMIN_PASSWORD and SERVER_PASSWORD
docker-compose up -d
```

### Python
```bash
cd server/
pip install -r requirements.txt
pip install ../multi_user/wheels/replication-0.9.10-py3-none-any.whl
python -m replication.server -p 5555 -apwd YOUR_ADMIN_PASS
```

## Firewall Configuration
```bash
sudo ufw allow 5555/tcp
sudo ufw allow 5556/tcp
sudo ufw allow 5557/tcp
```

## Server Management

| Task | Docker Command | Python Command |
|------|----------------|----------------|
| Start | `docker-compose up -d` | `python -m replication.server ...` |
| Stop | `docker-compose down` | Ctrl+C or `>> exit` |
| Logs | `docker-compose logs -f` | Check console or log file |
| Restart | `docker-compose restart` | Stop and start again |

## Server Shell Commands (Interactive)
```
>> users     # List connected users
>> kick USER # Kick a user
>> exit      # Stop server
```

## Client Configuration in Blender

1. **Edit → Preferences → Add-ons → Multi-User**
2. Edit "Internet Server (Configure Me)" preset:
   - **IP**: Your server's public IP/domain
   - **Port**: 5555
   - **Admin Password**: From .env file
   - **Server Password**: From .env file (if set)
3. **Save preferences**

## Connecting from Blender

1. **N** → Multi-User tab
2. Select your server from dropdown
3. Click **Join Session**

## Testing Connection
```bash
python server/test_connection.py YOUR_SERVER_IP 5555
```

## Common Issues

| Problem | Solution |
|---------|----------|
| Connection timeout | Check firewall, verify server is running |
| Auth failed | Double-check passwords in .env |
| Can't edit object | Object owned by another user |
| High latency | Increase timeout in Multi-User preferences |

## Ports Reference

| Port | Purpose | Protocol |
|------|---------|----------|
| 5555 | Command channel | TCP |
| 5556 | Data replication | TCP |
| 5557 | Heartbeat/TTL | TCP |

## Environment Variables (.env)

```bash
ADMIN_PASSWORD=your_secure_password
SERVER_PASSWORD=optional_server_password
PORT=5555
LOG_LEVEL=INFO
TIMEOUT=10000
```

## File Locations

| File | Purpose |
|------|---------|
| `server/README.md` | Full documentation |
| `server/CLIENT_SETUP.md` | Client configuration guide |
| `server/.env` | Server configuration |
| `server/docker-compose.yml` | Docker setup |
| `server/deploy.sh` | Automated deployment |

## Security Checklist

- [ ] Set strong ADMIN_PASSWORD
- [ ] Set SERVER_PASSWORD for private servers
- [ ] Configure firewall (only ports 5555-5557)
- [ ] Use HTTPS proxy for encryption (optional)
- [ ] Keep passwords secure (don't share publicly)

## Performance Tips

**Server:**
- Use adequate CPU/RAM (2+ cores, 4GB+ RAM)
- Monitor with `docker stats`

**Client:**
- Increase timeout for slow connections
- Disable "Sync During Edit Mode" for large meshes
- Reduce update frequency in preferences

## Getting Your Server's Public IP
```bash
curl ifconfig.me
```

## Log Locations

| Deployment | Log Location |
|------------|--------------|
| Docker | `docker-compose logs -f` |
| Python | `multi_user_server.log` |
| Systemd | `/var/log/blender-multiuser/` |

---

**For detailed guides, see [README.md](README.md) and [CLIENT_SETUP.md](CLIENT_SETUP.md)**
