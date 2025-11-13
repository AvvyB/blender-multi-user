# Quick Deploy - Persistent Storage v2 Fix

## What This Fixes
**Critical Bug**: Data only persisted if Blender stayed open. Now data persists on server independently.

---

## Deploy (3 Minutes)

### On Your Local Machine
```bash
cd ~/Projects/multi-user
rsync -avz --progress server/ root@your-server-ip:~/blender-server/
```

### On Your Server
```bash
ssh root@your-server-ip
cd ~/blender-server
docker-compose down
docker-compose build --no-cache
docker-compose up -d
docker-compose logs --tail 50
```

**Look for**:
```
Multi-User Blender Server with Persistent Storage v2
✓ Persistence hooks applied
✓ Auto-save enabled (interval: 120s)
```

---

## Test (5 Minutes)

1. **Connect from Blender** → Click "Init"
2. **Create test objects** → Wait 3 minutes
3. **Check auto-save**: `docker-compose logs | grep "Session saved"`
4. **Close ALL Blender clients**
5. **Restart server**: `docker-compose restart`
6. **Check logs**: `docker-compose logs --tail 30`
   - Should see: `✓ Repository automatically initialized to ACTIVE state`
7. **Reconnect** → No Init button, all objects still there ✅

---

## Quick Checks

### Is v2 running?
```bash
docker-compose logs | grep "Persistent Storage v2"
```

### Is auto-save working?
```bash
docker-compose logs | grep "Session saved"
# Should appear every 2 minutes
```

### Will auto-init happen?
```bash
cat ~/blender-server/data/session_metadata.json | grep initialized
# Should show: "initialized": true
```

---

## If Problems

### Data Still Lost
```bash
# Check saves are happening
docker-compose logs -f | grep "Session saved"

# Check disk space
df -h

# Check data directory exists
ls -lh ~/blender-server/data/
```

### Init Button Still Appears
```bash
# Check if session was initialized before restart
cat ~/blender-server/data/session_metadata.json

# If "initialized": false, click Init once
# Then it will auto-init on future restarts
```

### Full Debug
```bash
# Capture all logs
docker-compose logs > ~/server-debug.log

# Check for errors
grep -i error ~/server-debug.log
```

---

## Success = These 4 Signs

1. ✅ Logs show "Persistent Storage v2"
2. ✅ Logs show "Session saved" every 2 minutes
3. ✅ After restart: "Repository automatically initialized"
4. ✅ Reconnect: No Init button, data preserved

---

**Ready to deploy? Follow the commands above!**
