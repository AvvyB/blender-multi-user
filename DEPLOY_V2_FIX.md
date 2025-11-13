# Deploy Persistent Storage v2 Fix

## What This Fixes

**Critical Issue**: Server was losing all data when all Blender clients disconnected. Data only persisted if at least one client stayed connected.

**Root Cause**: The old persistent_server.py used unreliable monkey-patching. The server wasn't actually saving data independently.

**Solution**: persistent_server_v2.py uses a robust approach with:
- Global server instance capture
- Direct repository access
- Independent auto-save thread running every 2 minutes
- Saves even when no clients are connected

---

## Deployment Steps

### 1. Upload Files to Server

From your local machine, sync the updated files to your server:

```bash
# Upload the entire server directory
cd ~/Projects/multi-user
rsync -avz --progress server/ root@your-server-ip:~/blender-server/

# Or if you prefer scp for specific files:
scp server/persistent_server_v2.py root@your-server-ip:~/blender-server/
scp server/Dockerfile root@your-server-ip:~/blender-server/
scp server/docker-compose.yml root@your-server-ip:~/blender-server/
```

### 2. Deploy on Server

SSH into your server and rebuild:

```bash
ssh root@your-server-ip

cd ~/blender-server

# Stop current server
docker-compose down

# Rebuild with new code (force clean build)
docker-compose build --no-cache

# Start server
docker-compose up -d

# View startup logs
docker-compose logs --tail 50
```

### 3. Verify Server Started Correctly

Check the logs for the v2 startup banner:

```bash
docker-compose logs | grep -A 10 "Persistent Storage v2"
```

You should see:
```
======================================================================
Multi-User Blender Server with Persistent Storage v2
======================================================================

📁 Data Directory: /app/data
⏱️  Auto-save Interval: 120 seconds
💾 Max Backups: 10

✓ Persistence hooks applied
✓ Auto-save enabled (interval: 120s)
🚀 Starting replication server...
```

---

## Testing the Fix

### Test 1: Data Persists When All Clients Disconnect

This is the critical test for the bug you reported.

**Steps**:
1. **Connect from Blender**
   - Open Blender
   - Go to Multi-User panel
   - Click "Connect" to your server
   - Click "Init" button (first time only)

2. **Create Test Data**
   - Add some objects (Cube, Sphere, etc.)
   - Move them around
   - Rename them so you can recognize them
   - Wait at least 3 minutes for auto-save to run

3. **Verify Auto-Save is Working**
   ```bash
   # On server, check logs for auto-save messages
   docker-compose logs | grep "Session saved"
   ```

   Should see:
   ```
   ✓ Session saved to disk (reason: auto-save)
   ```

4. **Close ALL Blender Clients**
   - Close Blender completely
   - ALL users should disconnect
   - Wait 30 seconds

5. **Restart Server**
   ```bash
   docker-compose restart
   ```

6. **Check Server Logs After Restart**
   ```bash
   docker-compose logs --tail 30
   ```

   Should see:
   ```
   📂 Previous session found:
      Timestamp: 2025-01-12T15:30:45
      Initialized: True
      Nodes: 47
      Reason: auto-save

      → Session will be automatically restored on startup

   ✓ Repository graph restored
   ✓ Repository metadata restored
   ✓ Repository automatically initialized to ACTIVE state
      Users can connect immediately without re-initialization
   ```

7. **Reconnect from Blender**
   - Open Blender again
   - Click "Connect"
   - **Check**: No "Init" button should appear
   - **Check**: All your test objects should still be there!

**Expected Result**: ✅ All data preserved, no Init button needed

**If it fails**: Data is lost or Init button appears - report back the server logs

---

### Test 2: Verify Continuous Auto-Save

**Steps**:
1. Connect from Blender
2. Keep Blender open
3. Watch server logs for auto-save:
   ```bash
   docker-compose logs -f | grep "Session saved"
   ```

**Expected Result**: Every 2 minutes you should see:
```
✓ Session saved to disk (reason: auto-save)
```

**Note**: Even if no changes are made, it still saves (ensures data is always current)

---

### Test 3: Save on User Disconnect

**Steps**:
1. Connect from Blender
2. Create/modify objects
3. Disconnect by clicking "Disconnect" button
4. Check server logs:
   ```bash
   docker-compose logs --tail 10
   ```

**Expected Result**:
```
User disconnected: YourUsername
✓ Session saved to disk (reason: user_disconnect:YourUsername)
```

---

### Test 4: Multiple Users Scenario

**Steps**:
1. Connect from **2 different Blender instances** (or 2 computers)
2. Both users create objects
3. **Disconnect both users** completely
4. Wait 1 minute
5. **Restart server**
6. **Both users reconnect**

**Expected Result**: Both users see all objects created by both users, no Init button

---

## Monitoring

### Check Current Session Status

```bash
# View metadata file (human-readable)
cat ~/blender-server/data/session_metadata.json
```

Example output:
```json
{
  "timestamp": 1736695945.123,
  "datetime": "2025-01-12T15:32:25",
  "reason": "auto-save",
  "initialized": true,
  "node_count": 47
}
```

**Key field**: `"initialized": true` means auto-init will happen on restart

### Check Backups

```bash
# List all backup snapshots
ls -lh ~/blender-server/data/backups/
```

Example:
```
snapshot_20250112_143225.pkl
snapshot_20250112_143425.pkl
snapshot_20250112_143625.pkl
```

You should have up to 10 backups (configurable via MAX_BACKUPS)

### View Live Logs

```bash
# Watch logs in real-time
docker-compose logs -f

# Filter for save events
docker-compose logs -f | grep -E "(saved|restored|initialized)"
```

### Check Data Directory

```bash
ls -lh ~/blender-server/data/
```

Should contain:
- `session_snapshot.pkl` - Latest session (binary)
- `session_metadata.json` - Human-readable metadata
- `backups/` - Directory with timestamped backups

---

## Troubleshooting

### Issue: Still Losing Data

**Check**:
1. Verify v2 is running:
   ```bash
   docker-compose logs | grep "Persistent Storage v2"
   ```

2. Verify auto-save is running:
   ```bash
   docker-compose logs | grep "Auto-save enabled"
   ```

3. Check if saves are happening:
   ```bash
   docker-compose logs | grep "Session saved"
   ```

4. Check data directory permissions:
   ```bash
   ls -ld ~/blender-server/data/
   # Should be writable
   ```

5. Check disk space:
   ```bash
   df -h
   ```

**If still failing**: Capture logs and share:
```bash
docker-compose logs > ~/server-debug.log
# Send server-debug.log for analysis
```

---

### Issue: "Init" Button Still Appears

**Causes**:
1. **Session was never initialized before restart**
   - Check metadata: `cat data/session_metadata.json | grep initialized`
   - If `"initialized": false`, you need to click Init once
   - After that, restarts won't need Init

2. **Server didn't restore session**
   - Check logs for: `"Previous session found"`
   - Check logs for: `"Repository automatically initialized"`

3. **Snapshot doesn't exist**
   - Check: `ls data/session_snapshot.pkl`
   - If missing, click Init once to create it

**Fix**: If initialized=false, just click Init once. After that, future restarts will auto-initialize.

---

### Issue: Auto-Save Not Running

**Check server logs for**:
```bash
docker-compose logs | grep -E "(Auto-save enabled|Session saved)"
```

**Should see**:
- At startup: `✓ Auto-save enabled (interval: 120s)`
- Every 2 min: `✓ Session saved to disk`

**If missing**:
1. Verify persistent_server_v2.py is being used:
   ```bash
   docker-compose logs | head -20
   ```

2. Check for errors:
   ```bash
   docker-compose logs | grep -i error
   ```

---

### Issue: "Server instance captured" Not in Logs

**Symptom**: Logs don't show `"Server instance captured for persistence"`

**Cause**: Persistence hooks didn't apply correctly

**Fix**:
1. Check for hook errors:
   ```bash
   docker-compose logs | grep -i "hook"
   ```

2. Rebuild from scratch:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

---

## Configuration

### Change Auto-Save Interval

Edit `docker-compose.yml`:

```yaml
environment:
  - SAVE_INTERVAL=60  # Save every 60 seconds instead of 120
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

### Change Number of Backups

Edit `docker-compose.yml`:

```yaml
environment:
  - MAX_BACKUPS=20  # Keep 20 backups instead of 10
```

### Disable Auto-Save (Not Recommended)

You can't fully disable auto-save, but you can set a very long interval:

```yaml
environment:
  - SAVE_INTERVAL=86400  # Save once per day
```

**Warning**: Longer intervals = more potential data loss on crash

---

## Recovery

### Restore from Backup

If you need to restore an older session:

```bash
# List backups
ls -lh ~/blender-server/data/backups/

# Copy backup to main snapshot
cd ~/blender-server/data
cp backups/snapshot_20250112_143225.pkl session_snapshot.pkl

# Restart server
docker-compose restart
```

### Clear All Data (Fresh Start)

```bash
docker-compose down
rm -rf ~/blender-server/data/*
docker-compose up -d
```

Server will start fresh, require Init button.

---

## Success Indicators

✅ **You'll know it's working when**:

1. Server logs show:
   ```
   Multi-User Blender Server with Persistent Storage v2
   ✓ Persistence hooks applied
   ✓ Auto-save enabled (interval: 120s)
   ```

2. Every 2 minutes in logs:
   ```
   ✓ Session saved to disk (reason: auto-save)
   ```

3. After closing ALL clients and restarting server:
   ```
   📂 Previous session found:
      Initialized: True
   ✓ Repository automatically initialized to ACTIVE state
   ```

4. When reconnecting:
   - No "Init" button
   - All objects still present
   - Can start working immediately

---

## Summary of Changes

| Feature | v1 (Old) | v2 (New) |
|---------|----------|----------|
| Save method | Monkey-patching | Direct repository access |
| Auto-save | Unreliable | Independent thread |
| Saves when disconnected | ❌ No | ✅ Yes |
| Server instance capture | Weak | Strong global reference |
| Reliability | Poor | High |

**Bottom Line**: v2 should fix the data loss issue completely. Data persists even when all clients disconnect.

---

## Need Help?

If after following these steps you still experience issues:

1. **Capture logs**:
   ```bash
   docker-compose logs > ~/server-logs.txt
   ```

2. **Capture metadata**:
   ```bash
   cat ~/blender-server/data/session_metadata.json
   ```

3. **Report**:
   - What test failed
   - Server logs
   - Metadata content
   - Steps you took

---

**Last Updated**: January 13, 2025
**Fixes**: Critical data loss bug
**Status**: Ready to deploy and test
