# Persistent Storage Guide

## Overview

The Multi-User server now includes **automatic persistent storage** that saves your session data to disk and recovers it after server restarts.

### Key Features

- ✅ **Auto-save every 2 minutes** (configurable)
- ✅ **Saves on user disconnect**
- ✅ **Automatic restore on startup**
- ✅ **Timestamped backups**
- ✅ **No manual intervention required**

---

## How It Works

### Automatic Saving

The server automatically saves session data in three scenarios:

1. **Every 2 minutes** (periodic auto-save)
2. **When a user disconnects** (user logout)
3. **On server shutdown** (graceful shutdown)

### Automatic Recovery

When the server starts:
- Checks for existing session snapshot
- Automatically restores latest session data
- Users connect and see the previous session state

### What Gets Saved

All session data is preserved:
- **Scene data** - All objects, materials, modifiers, etc.
- **Tasks** - All tasks and assignments
- **Chat messages** - Recent chat history
- **User metadata** - User information and state
- **Repository graph** - Complete scene graph structure

---

## Data Storage Location

### On Server (Docker)

Inside the container:
```
/app/data/
├── session_snapshot.pkl      # Latest session (auto-loaded)
├── session_metadata.json      # Human-readable session info
└── backups/                   # Timestamped backups
    ├── snapshot_20250112_143025.pkl
    ├── snapshot_20250112_143225.pkl
    └── ...
```

### On Host Machine

```
server/data/
├── session_snapshot.pkl
├── session_metadata.json
└── backups/
    └── ...
```

**Persistent across restarts** - Volume mounted in docker-compose.yml

---

## Configuration

### Environment Variables

Edit `server/.env`:

```bash
# Auto-save interval in seconds (default: 120 = 2 minutes)
SAVE_INTERVAL=120

# Maximum backup files to keep (default: 10)
MAX_BACKUPS=10
```

### Custom Save Intervals

```bash
# Save every 5 minutes
SAVE_INTERVAL=300

# Save every 30 seconds (frequent saves)
SAVE_INTERVAL=30

# Save every 10 minutes (less frequent)
SAVE_INTERVAL=600
```

### Backup Retention

```bash
# Keep last 20 backups
MAX_BACKUPS=20

# Keep last 5 backups (less disk space)
MAX_BACKUPS=5

# Keep last 50 backups (more history)
MAX_BACKUPS=50
```

---

## Usage

### Normal Operation

**No action required!** The server handles everything automatically.

When you see these log messages, persistence is working:

```
Session saved to disk (reason: auto-save)
  Snapshot: /app/data/session_snapshot.pkl
  Backup: /app/data/backups/snapshot_20250112_143225.pkl
```

### After Server Restart

1. **Server starts**
2. Server detects previous session:
   ```
   Previous session found:
     Timestamp: 2025-01-12T14:32:25
     Users: 3
     Nodes: 47
     Initialized: True
     Reason: user_disconnect:Alice

   Session will be automatically restored on first connection
   ```
3. **Server auto-initializes** (if previously initialized):
   ```
   Repository graph restored
   Repository metadata restored
   Repository automatically initialized to ACTIVE state
   Users can connect immediately without re-initialization
   ```
4. **Users reconnect**
5. **All previous work is restored** - objects, tasks, chat, etc.
6. **No "Init" button needed** - users connect directly to active session!

### Viewing Session Info

Check the metadata file to see session details:

```bash
cat server/data/session_metadata.json
```

Example output:
```json
{
  "timestamp": 1736695945.123,
  "datetime": "2025-01-12T14:32:25",
  "reason": "user_disconnect:Alice",
  "initialized": true,
  "user_count": 3,
  "node_count": 47
}
```

---

## Deployment

### New Deployment

Just deploy as normal - persistence is enabled by default:

```bash
cd server/
./prepare.sh
docker-compose up -d
```

The `data/` directory is automatically created.

### Upgrading Existing Server

1. **Stop the server**:
   ```bash
   docker-compose down
   ```

2. **Pull latest changes** (if from Git):
   ```bash
   git pull
   ```

3. **Rebuild container**:
   ```bash
   docker-compose build
   ```

4. **Start server**:
   ```bash
   docker-compose up -d
   ```

5. **Verify persistence is active**:
   ```bash
   docker-compose logs | grep "Auto-save enabled"
   ```

### Migrating Existing Data

If you have an old server without persistence, the new server starts fresh. No migration needed.

---

## Recovery Scenarios

### Scenario 1: Server Crash

**What happens**:
- Server crashes unexpectedly
- Last auto-save was 1 minute ago

**Result**:
- Restart server
- Session restored from last auto-save (1 minute old)
- Lost: Only changes in the last 1 minute

**Mitigation**: Use shorter `SAVE_INTERVAL` (e.g., 30 seconds)

### Scenario 2: Planned Restart

**What happens**:
- You run `docker-compose restart`
- Server receives shutdown signal
- Saves final snapshot before stopping

**Result**:
- All data saved
- Zero data loss
- Full recovery on restart

### Scenario 3: User Disconnects Unexpectedly

**What happens**:
- User's Blender crashes or network drops
- Server detects disconnect
- Saves session immediately

**Result**:
- Session saved with that user's latest changes
- When user reconnects, all their work is there

### Scenario 4: All Users Log Off

**What happens**:
- Last user disconnects
- Server saves session
- Server remains running with no users

**Result**:
- Session preserved
- Next user to connect sees the previous state
- Work continues seamlessly

---

## Backup Management

### Automatic Cleanup

Old backups are automatically deleted when `MAX_BACKUPS` is exceeded.

Example with `MAX_BACKUPS=10`:
```
backups/
├── snapshot_20250112_100000.pkl  ← Deleted when 11th backup is created
├── snapshot_20250112_102000.pkl  ← Kept (10 most recent)
├── snapshot_20250112_104000.pkl
├── ...
└── snapshot_20250112_143225.pkl  ← Newest (always kept)
```

### Manual Backup

To create a manual backup:

```bash
# Copy the current snapshot
cd server/data
cp session_snapshot.pkl manual_backup_$(date +%Y%m%d_%H%M%S).pkl
```

### Restore from Backup

To restore from a specific backup:

```bash
# 1. Stop the server
docker-compose down

# 2. Replace snapshot with backup
cd server/data
cp backups/snapshot_20250112_120000.pkl session_snapshot.pkl

# 3. Restart server
docker-compose up -d
```

---

## Disk Space Usage

### Snapshot Sizes

Typical snapshot sizes:
- **Empty scene**: ~10 KB
- **Small project** (< 100 objects): ~100 KB - 1 MB
- **Medium project** (100-1000 objects): 1-10 MB
- **Large project** (1000+ objects): 10-100 MB

### Total Disk Usage

With `MAX_BACKUPS=10` and 2-minute saves:
- **Time window**: 20 minutes of backups
- **Disk usage**: ~10 × snapshot_size

Example:
- Medium project (5 MB per snapshot)
- 10 backups = 50 MB total

### Cleanup

To manually clean old backups:

```bash
# Remove all backups older than 24 hours
find server/data/backups/ -name "snapshot_*.pkl" -mtime +1 -delete

# Remove all backups
rm server/data/backups/snapshot_*.pkl
```

---

## Monitoring

### Check Auto-Save Status

```bash
# View live logs
docker-compose logs -f

# Look for these messages:
# "Auto-save enabled (interval: 120s)"
# "Session saved to disk (reason: auto-save)"
# "Session saved to disk (reason: user_disconnect:Username)"
```

### Check Last Save Time

```bash
# View metadata
cat server/data/session_metadata.json

# Or check file modification time
ls -lh server/data/session_snapshot.pkl
```

### Check Backup Count

```bash
# Count backups
ls server/data/backups/ | wc -l

# List backups with dates
ls -lht server/data/backups/
```

---

## Troubleshooting

### Issue: Snapshots Not Being Created

**Check**:
1. Verify data directory exists:
   ```bash
   ls -la server/data/
   ```

2. Check Docker volume mount:
   ```bash
   docker inspect blender-multiuser-server | grep data
   ```

3. Check logs for errors:
   ```bash
   docker-compose logs | grep "Failed to save"
   ```

### Issue: Session Not Restoring

**Check**:
1. Verify snapshot exists:
   ```bash
   ls -lh server/data/session_snapshot.pkl
   ```

2. Check server logs on startup:
   ```bash
   docker-compose logs | grep "restore"
   ```

3. Check for corruption:
   ```bash
   # If snapshot is corrupted, restore from backup
   cp server/data/backups/snapshot_20250112_120000.pkl \
      server/data/session_snapshot.pkl
   ```

### Issue: Disk Space Running Out

**Solutions**:
1. Reduce `MAX_BACKUPS`:
   ```bash
   # In .env
   MAX_BACKUPS=5
   ```

2. Increase `SAVE_INTERVAL`:
   ```bash
   # In .env
   SAVE_INTERVAL=300  # 5 minutes
   ```

3. Clean old backups:
   ```bash
   rm server/data/backups/snapshot_2025*.pkl
   ```

### Issue: Snapshots Too Large

**Causes**:
- Very large scenes with many objects
- High-resolution textures in scene

**Solutions**:
1. Increase `SAVE_INTERVAL` to reduce backup frequency
2. Reduce `MAX_BACKUPS` to keep fewer backups
3. Manually archive old backups to external storage

---

## Security Considerations

### Data Privacy

- Snapshots contain **all session data**
- Store backups securely
- Consider encrypting the data directory for sensitive projects

### Backup Encryption (Optional)

```bash
# Encrypt backups directory
tar -czf - server/data/backups | \
  openssl enc -aes-256-cbc -out backups_encrypted.tar.gz.enc

# Decrypt backups
openssl enc -aes-256-cbc -d -in backups_encrypted.tar.gz.enc | \
  tar -xzf -
```

---

## Performance Impact

### CPU Usage

- **Minimal** - Saves run in background thread
- Typical: <1% CPU during save
- No impact on client connections

### Memory Usage

- **Negligible** - Snapshot creation is efficient
- Typical: <10 MB additional memory

### Network Impact

- **None** - Saves are local disk operations
- No network traffic generated

### Save Duration

Typical save times:
- Small project (<1 MB): <0.1 seconds
- Medium project (1-10 MB): 0.1-0.5 seconds
- Large project (10-100 MB): 0.5-2 seconds

Saves do **not** block client connections.

---

## Best Practices

### 1. Regular Monitoring

Check logs weekly:
```bash
docker-compose logs --tail 100 | grep "Session saved"
```

### 2. Test Recovery

Periodically test recovery:
```bash
# 1. Note current state
# 2. Restart server
docker-compose restart
# 3. Verify session restored
docker-compose logs | grep "restored"
```

### 3. External Backups

For critical projects, copy backups externally:
```bash
# Daily backup to external storage
rsync -av server/data/backups/ /path/to/external/backup/
```

### 4. Adjust Settings

Tune settings based on your needs:
- **Frequent changes**: Lower `SAVE_INTERVAL` (30-60s)
- **Stable sessions**: Higher `SAVE_INTERVAL` (300-600s)
- **Disk constrained**: Lower `MAX_BACKUPS` (3-5)
- **Want history**: Higher `MAX_BACKUPS` (20-50)

---

## Migration Guide

### Disabling Persistence (Not Recommended)

If you need to disable persistence:

1. Edit `Dockerfile`, change CMD to:
   ```dockerfile
   CMD python -m replication.server \
       --port ${PORT} \
       --admin-password ${ADMIN_PASSWORD} \
       --server-password ${SERVER_PASSWORD} \
       --log-level ${LOG_LEVEL} \
       --timeout ${TIMEOUT}
   ```

2. Rebuild:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

### Re-enabling Persistence

Revert the Dockerfile change and rebuild.

---

## FAQ

**Q: Does persistence slow down the server?**
A: No, saves happen in the background with negligible impact.

**Q: Can I access snapshots from outside Docker?**
A: Yes, they're in `server/data/` on the host machine.

**Q: What happens if snapshot is corrupted?**
A: Server automatically falls back to a backup from `backups/` directory.

**Q: Can I manually trigger a save?**
A: Not directly, but disconnecting/reconnecting a user triggers a save.

**Q: Do snapshots include Blender files?**
A: They contain the scene graph data, not .blend files. Users should still save their local .blend files.

**Q: How much history is kept?**
A: By default, last 10 snapshots × 2-minute intervals = 20 minutes of history.

**Q: Can I increase backup retention?**
A: Yes, set `MAX_BACKUPS=50` or higher in `.env`.

**Q: What if server is killed (kill -9)?**
A: Last auto-save is used (max 2 minutes old by default).

---

## Support

For issues with persistent storage:

1. Check server logs: `docker-compose logs`
2. Verify data directory: `ls -la server/data/`
3. Check configuration: `cat server/.env`
4. Report issues with log excerpts

---

**Version**: 1.0
**Last Updated**: January 12, 2025
**Compatible**: Multi-User v0.8.1+
