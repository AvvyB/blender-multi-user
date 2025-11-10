# Client Setup Guide

How to connect Blender to your internet-hosted Multi-User server.

## Prerequisites

- Blender 4.2+ with Multi-User addon installed
- Server IP address or domain name
- Server password (if required)
- Admin password (if you need admin privileges)

## Step-by-Step Connection

### 1. Open Blender Preferences

1. Open Blender
2. Go to **Edit → Preferences**
3. Select **Add-ons** from the left sidebar
4. Find and expand the **Multi-User** addon

### 2. Configure Server Preset

You'll see a preset called **"Internet Server (Configure Me)"** - edit it:

1. Click on the preset to expand it
2. Update the following fields:

   | Field | Value | Example |
   |-------|-------|---------|
   | **Server Name** | A friendly name | "My Cloud Server" |
   | **IP** | Your server's public IP or domain | `123.45.67.89` or `myserver.com` |
   | **Port** | Server port (usually 5555) | `5555` |
   | **Use Admin Password** | Check if you have admin access | ✓ |
   | **Admin Password** | The admin password from server setup | `your-admin-password` |
   | **Use Server Password** | Check if server requires password | ✓ (if needed) |
   | **Server Password** | The server password (if set) | `your-server-password` |

3. Click outside the fields to save

### 3. Connect to the Server

1. **Save your current Blender file** (important!)

2. In Blender, open the **Multi-User** sidebar:
   - Press `N` to open the sidebar
   - Click the **Multi-User** tab

3. In the **Session** panel:
   - Select your server from the **Server** dropdown
   - Click **Join Session**

4. Wait for connection (watch the status in the panel)

5. When connected, you'll see:
   - Your username listed
   - Other connected users
   - Real-time cursor positions of other users

## Testing Your Connection

### Before connecting from Blender, test with Python:

```bash
# From your local machine
python server/test_connection.py YOUR_SERVER_IP 5555
```

This will verify all three ports (5555, 5556, 5557) are accessible.

## Troubleshooting

### "Connection timeout" error

**Possible causes:**
- Server is not running
- Firewall blocking ports
- Incorrect IP address

**Solutions:**
1. Verify server is running:
   ```bash
   ssh user@your-server
   docker-compose ps
   ```

2. Test connectivity:
   ```bash
   telnet YOUR_SERVER_IP 5555
   ```

3. Check firewall on server:
   ```bash
   sudo ufw status
   ```

### "Authentication failed" error

**Possible causes:**
- Wrong password
- Password mismatch

**Solutions:**
1. Double-check passwords (no trailing spaces!)
2. Verify password in server's `.env` file
3. Restart server after changing passwords:
   ```bash
   docker-compose restart
   ```

### "Version mismatch" error

**Cause:**
- Client and server have different replication library versions

**Solution:**
- Ensure all users have the same version of the Multi-User addon
- Update addon to latest version on all clients

### Objects not syncing

**Possible causes:**
- Object ownership conflicts
- Network latency
- Object locked by another user

**Solutions:**
1. Check object ownership (highlighted in viewport)
2. Right-click → Multi-User → Take Ownership (if admin)
3. Check network latency in the Multi-User panel

## Usage Tips

### Ownership System

- **Selected objects** are automatically locked to you
- Other users see a colored outline around your objects
- **Admin users** can take ownership from others
- **Common objects** can be edited by anyone

### Performance Optimization

For slow connections:

1. In Multi-User preferences:
   - Increase **Connection Timeout** to 10000ms
   - Reduce **Depsgraph Update Rate** to 2-3 seconds
   - Disable **Sync During Edit Mode** for complex meshes

2. In Blender:
   - Use smaller scene files when possible
   - Minimize texture size
   - Reduce polygon count

### Collaborative Workflow

**Best Practices:**
1. **Communicate** who is working on what
2. **Commit changes** by deselecting objects when done
3. **Save frequently** - local saves don't affect others
4. **Use layers/collections** to separate work areas
5. **Designate an admin** for conflict resolution

### Security

**For sensitive projects:**
1. Always use a server password
2. Use a strong admin password
3. Consider VPN for additional security
4. Don't share credentials over insecure channels

## Network Requirements

### Bandwidth

Typical usage:
- **Initial sync**: Depends on scene size (MB-GB)
- **Real-time updates**: 10-100 KB/s per user
- **Viewport sync**: 1-5 KB/s per user

### Latency

- **Good**: < 50ms (same region)
- **Acceptable**: 50-200ms (continental)
- **Usable**: 200-500ms (intercontinental)
- **Challenging**: > 500ms (use higher timeouts)

Test latency:
```bash
ping YOUR_SERVER_IP
```

## Advanced: Port Forwarding (if hosting from home)

If you're hosting the server on your home network without a cloud provider:

### 1. Find your router's admin page
- Usually `192.168.1.1` or `192.168.0.1`

### 2. Set up port forwarding rules:

| Service Name | External Port | Internal Port | Internal IP | Protocol |
|--------------|---------------|---------------|-------------|----------|
| Blender CMD | 5555 | 5555 | [server IP] | TCP |
| Blender Data | 5556 | 5556 | [server IP] | TCP |
| Blender HB | 5557 | 5557 | [server IP] | TCP |

### 3. Find your public IP:
```bash
curl ifconfig.me
```

### 4. Give this IP to your collaborators

**Note:** Home internet IPs often change. Consider:
- Dynamic DNS service (No-IP, DuckDNS)
- Static IP from ISP (usually paid)

## Getting Help

**Server not working?**
1. Check server logs: `docker-compose logs`
2. Run connection test: `python test_connection.py`
3. Verify firewall rules

**Connection issues?**
1. Test with `telnet SERVER_IP 5555`
2. Check Blender System Console for errors
3. Increase timeout in Multi-User preferences

**Sync issues?**
1. Check ownership colors in viewport
2. Verify network latency
3. Try disconnecting and rejoining

## Video Tutorial

For a visual guide, check out:
- Multi-User addon documentation
- Blender's Multi-User addon wiki

---

**Happy Collaborating!** 🎨
