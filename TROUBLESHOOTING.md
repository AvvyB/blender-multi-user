# Multi-User Troubleshooting Guide

## v0.8.1 - Diagnostics & Error Resolution

This guide helps you diagnose and fix common Multi-User issues, especially connection errors and version mismatches.

---

## 🔧 New Diagnostics Tool (v0.8.1+)

### How to Use Diagnostics

1. **Connect to server** (or attempt to connect)
2. **Open Multi-User panel** (press `N` in 3D viewport)
3. **Click "Diagnostics" button** (below the Disconnect button)

### What Diagnostics Shows

The diagnostics popup displays:

- **Addon Version** - Your Multi-User extension version
- **Replication Library** - Core library version (should be 0.9.10)
- **Python Version** - Python version used by Blender
- **Blender Version** - Your Blender version
- **Connection Status** - Whether you're connected
- **Online Users** - List of all connected users
- **Dependencies** - Status of required libraries (ZeroMQ, DeepDiff, OrderlySet)

### What to Look For

✅ **All checks green** = Everything is working correctly

❌ **Red indicators**:
- Missing dependencies → Reinstall extension
- Version mismatches → See version troubleshooting below

---

## 🚨 Common Error: Pickle Unpickling Errors

### Symptoms

Server logs show:
```
_pickle.UnpicklingError: invalid load key, '\x16'.
EOFError: Ran out of input
Corrupted data frame received
```

### Root Causes

1. **Version mismatch between clients**
2. **Network packet corruption**
3. **Incomplete data transmission**
4. **Firewall interference**

### Solution Steps

#### Step 1: Verify All Clients Use Same Version

Run diagnostics on **ALL connected clients**:

1. On each client, click **Diagnostics**
2. Note the **Addon Version** and **Replication Library** version
3. Compare versions across all clients

**Fix**: All clients must use the **exact same version**:
- If mixed: Have everyone upgrade to v0.8.1
- Uninstall old version first, then install new one

#### Step 2: Clean Restart

1. **Disconnect all clients** from server
2. **Restart server**:
   ```bash
   docker-compose restart
   ```
3. **Wait 10 seconds** for server to fully start
4. **Reconnect clients one at a time**
5. Monitor server logs for errors

#### Step 3: Check Network Connection

```bash
# From client machine, test connection to server
ping your-server-ip.com

# Check if ports are accessible
telnet your-server-ip.com 5555
telnet your-server-ip.com 5556
telnet your-server-ip.com 5557
```

If any fail:
- **Check firewall rules** on server
- **Verify ports 5555-5557 are open**
- **Check network stability** (packet loss)

#### Step 4: Increase Timeout

If network is slow or unreliable:

1. **Edit server `.env` file**:
   ```bash
   TIMEOUT=30000
   ```
   (Changed from default 10000 to 30000ms)

2. **Restart server**:
   ```bash
   docker-compose restart
   ```

---

## 🚨 Error: Heartbeat Unpacking

### Symptoms

```
ValueError: too many values to unpack (expected 2)
```

### Cause

Network issue causing malformed heartbeat packets.

### Solution

Same as pickle errors above. Follow all 4 steps.

---

## 🚨 Error: Connection Timeout

### Symptoms

- Client hangs on "Connecting..."
- No error message, just timeout
- Server logs show no connection attempt

### Solutions

1. **Check server is running**:
   ```bash
   docker-compose ps
   ```
   Should show "Up" status

2. **Check server logs**:
   ```bash
   docker-compose logs -f
   ```
   Should show "Server listening on port 5555"

3. **Verify IP address in client**:
   - Multi-User → Edit server preset
   - Ensure IP matches your actual server
   - For internet servers: Use domain name or public IP
   - For local: Use "localhost" or "127.0.0.1"

4. **Check ports are accessible**:
   ```bash
   # On server machine
   netstat -tulpn | grep 5555
   ```
   Should show Docker listening on ports

5. **Firewall rules**:
   ```bash
   # On server machine (Ubuntu/Debian)
   sudo ufw allow 5555:5557/tcp
   sudo ufw reload
   ```

---

## 🚨 Error: "Replication Library: Not found"

### Symptoms

Diagnostics shows "Replication Library: Not found" with red error icon.

### Cause

Corrupted installation or missing dependencies.

### Solution

1. **Uninstall extension**:
   - Edit → Preferences → Extensions
   - Find "Multi-User"
   - Click dropdown → Remove

2. **Restart Blender**

3. **Reinstall extension**:
   - Download fresh `multi_user-0.8.1.zip`
   - Edit → Preferences → Extensions
   - Install from Disk
   - Select the .zip file

4. **Verify installation**:
   - Run Diagnostics
   - All dependencies should show green checkmarks

---

## 🚨 Error: Dependencies Missing

### Symptoms

Diagnostics shows missing ZeroMQ, DeepDiff, or OrderlySet.

### Solution

Same as "Replication Library: Not found" above - reinstall extension.

---

## 🔍 Debugging Server Issues

### Enable Debug Logging

Edit server `.env`:
```bash
LOG_LEVEL=DEBUG
```

Restart server:
```bash
docker-compose restart
```

### View Real-Time Logs

```bash
docker-compose logs -f
```

### Look for These Patterns

**Good signs**:
```
INFO: Server listening on port 5555
INFO: User 'Alice' connected
INFO: Broadcasting to 3 users
```

**Bad signs**:
```
ERROR: Failed to unpickle data
ERROR: Connection reset by peer
WARNING: Heartbeat timeout for user 'Bob'
```

### Search Logs for Errors

```bash
# Show only errors
docker-compose logs | grep ERROR

# Show errors and warnings
docker-compose logs | grep -E "(ERROR|WARNING)"

# Show last 100 lines with errors
docker-compose logs --tail 100 | grep ERROR
```

---

## 🔍 Debugging Client Issues

### Enable Blender Console (Windows)

1. Window → Toggle System Console
2. All Multi-User logs appear here

### Enable Blender Console (Mac/Linux)

Run Blender from terminal:
```bash
# Mac
/Applications/Blender.app/Contents/MacOS/Blender

# Linux
blender
```

Client logs appear in terminal.

### Look for Client Errors

```
ERROR: Failed to connect to server
ERROR: Timeout waiting for response
ERROR: Invalid data received
```

---

## 📋 Pre-Flight Checklist

Before reporting issues, verify:

- [ ] All clients use **same Multi-User version**
- [ ] Server is **running** (docker-compose ps)
- [ ] Ports **5555-5557 are open** on firewall
- [ ] Server IP/hostname is **correct** in client
- [ ] **Ran diagnostics** on all clients
- [ ] All dependencies show **green checkmarks**
- [ ] **Restarted server** and clients
- [ ] Checked **server logs** for errors
- [ ] Network connection is **stable** (no packet loss)

---

## 🆘 Version Compatibility Matrix

| Client Version | Server Version | Status |
|----------------|----------------|--------|
| v0.8.1 | Any (replication 0.9.10) | ✅ Recommended |
| v0.8.0 | Any (replication 0.9.10) | ✅ Compatible |
| v0.7.0 | Any (replication 0.9.10) | ✅ Compatible (no new features) |
| Mixed (0.7 + 0.8) | Any (replication 0.9.10) | ⚠️ May cause pickle errors |
| v0.8.1 | Old server (<0.9.10) | ❌ Incompatible |

**Best practice**: Always use matching versions across all clients.

---

## 🔄 Version Upgrade Procedure

### For All Team Members

1. **Coordinate upgrade time** (all disconnect)
2. **Download v0.8.1** from releases
3. **Uninstall old version**:
   - Edit → Preferences → Extensions
   - Remove "Multi-User"
4. **Restart Blender**
5. **Install v0.8.1**:
   - Extensions → Install from Disk
   - Select `multi_user-0.8.1.zip`
6. **Run diagnostics** to verify
7. **Reconnect to server**

### For Server (Optional)

Server doesn't need updating for v0.8.1, but if you want to restart:

```bash
cd server/
docker-compose restart
```

---

## 💡 Tips for Stable Connections

### For Internet Servers

1. **Use domain names** instead of IP addresses
2. **Enable SSL/TLS** via reverse proxy (Nginx, Caddy)
3. **Increase timeout** to 30000ms for slower connections
4. **Monitor bandwidth** - ensure adequate upload/download speed

### For Local Networks

1. **Use static IP** for server machine
2. **Disable firewall** on trusted local network (or open ports)
3. **Use wired ethernet** instead of WiFi when possible
4. **Keep clients on same network segment**

### For All Deployments

1. **Limit scene complexity** - fewer objects = less data to sync
2. **Use "Select Synced Objects"** to see what's syncing
3. **Monitor server logs** regularly for warnings
4. **Test with 2 clients first** before scaling up
5. **Ensure adequate server resources** (2GB RAM minimum)

---

## 📞 Getting Help

### Before Asking for Help

1. **Run diagnostics** on all clients
2. **Check server logs** for errors
3. **Try troubleshooting steps** above
4. **Note exact error messages**
5. **Check if all clients have same version**

### Information to Include

When reporting issues, provide:

- **Addon version** (from diagnostics)
- **Replication version** (from diagnostics)
- **Blender version** (from diagnostics)
- **Operating system** (Windows/Mac/Linux)
- **Server logs** (last 50 lines)
- **Client error messages**
- **Steps to reproduce**
- **Number of connected clients**
- **Network setup** (local/internet)

### Where to Get Help

- GitHub Issues: Report bugs and feature requests
- Documentation: Check all `.md` files in repository
- Server logs: Often reveal the root cause

---

## ✅ Success Indicators

You know everything is working when:

- ✅ Diagnostics show all green checkmarks
- ✅ All users see each other in online users list
- ✅ Changes sync instantly (<1 second)
- ✅ No errors in server logs
- ✅ Chat messages appear immediately
- ✅ Tasks sync to all users
- ✅ Keyframes sync in real-time
- ✅ Scene switching works smoothly

---

**Version**: v0.8.1
**Last Updated**: January 12, 2025
**Prepared for**: Multi-User Blender Extension
