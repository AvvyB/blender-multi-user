# Deploy Persistent Storage to Your Server

## 🎯 Goal

Add automatic session persistence to your existing Multi-User server so you never lose data on restart.

---

## 📦 What Changed

### New Files Created
- `server/persistent_server.py` - Persistent storage wrapper
- `server/PERSISTENT_STORAGE.md` - Full documentation
- `server/UPGRADE_TO_PERSISTENT.md` - Detailed upgrade guide
- `server/update_server.sh` - Automated update script
- `PERSISTENT_STORAGE_SUMMARY.md` - Quick reference

### Modified Files
- `server/Dockerfile` - Uses persistent_server.py
- `server/docker-compose.yml` - Added data volume mount
- `server/.env.example` - Added SAVE_INTERVAL and MAX_BACKUPS
- `server/README.md` - Added persistent storage section

---

## 🚀 Quick Deploy (Recommended)

### Option 1: Automated Script

**On your local machine**, upload files and run script:

```bash
# 1. Upload new files to server
scp server/persistent_server.py user@your-server.com:~/blender-server/
scp server/Dockerfile user@your-server.com:~/blender-server/
scp server/docker-compose.yml user@your-server.com:~/blender-server/
scp server/.env.example user@your-server.com:~/blender-server/
scp server/update_server.sh user@your-server.com:~/blender-server/
scp server/PERSISTENT_STORAGE.md user@your-server.com:~/blender-server/
scp server/UPGRADE_TO_PERSISTENT.md user@your-server.com:~/blender-server/

# 2. SSH to server and run update script
ssh user@your-server.com
cd ~/blender-server
chmod +x update_server.sh
./update_server.sh
```

**That's it!** The script handles everything:
- Backs up current setup
- Updates .env
- Rebuilds container
- Starts server with persistence
- Verifies it's working

---

## 🔧 Manual Deploy (Alternative)

If you prefer manual control:

### Step 1: SSH to Your Server

```bash
ssh user@your-server.com
cd ~/blender-server
```

### Step 2: Backup Current Setup

```bash
tar -czf backup_$(date +%Y%m%d).tar.gz .
ls -lh backup_*.tar.gz
```

### Step 3: Stop Server

```bash
docker-compose down
```

### Step 4: Upload New Files

From your local machine:

```bash
scp server/persistent_server.py user@your-server.com:~/blender-server/
scp server/Dockerfile user@your-server.com:~/blender-server/
scp server/docker-compose.yml user@your-server.com:~/blender-server/
```

### Step 5: Update .env

On your server:

```bash
cat >> .env << 'EOF'

# === Persistent Storage Settings ===
SAVE_INTERVAL=120
MAX_BACKUPS=10
EOF
```

### Step 6: Rebuild and Start

```bash
# Rebuild container
docker-compose build

# Start server
docker-compose up -d

# Check logs
docker-compose logs -f
```

Look for: `Auto-save enabled (interval: 120s)`

---

## ✅ Verification

### 1. Check Server Started

```bash
docker-compose ps
```

Should show `Up` status.

### 2. Check Logs

```bash
docker-compose logs | grep -E "(Persistent Storage|Auto-save)"
```

Should see:
```
Multi-User Blender Server with Persistent Storage
Data Directory: /app/data
Auto-save Interval: 120 seconds
Auto-save enabled (interval: 120s)
```

### 3. Check Data Directory

```bash
ls -la data/
```

Should see `backups/` directory.

### 4. Wait for First Save

After 2 minutes (or when a user connects/disconnects):

```bash
ls -lh data/
```

Should see:
- `session_snapshot.pkl`
- `session_metadata.json`
- `backups/snapshot_*.pkl`

### 5. Test Recovery

```bash
# Restart server
docker-compose restart

# Check if session restored
docker-compose logs | grep "restored"
```

Should see:
```
Session restored from disk
  Timestamp: 2025-01-12T14:32:25
  Users: X
```

---

## 🎮 How to Use

### Normal Usage

**Nothing changes for users!** They connect as normal.

Server now automatically:
- Saves every 2 minutes
- Saves when users disconnect
- Saves on shutdown
- Restores on startup

### After Server Restart

1. Server starts and restores previous session
2. Users reconnect
3. **All previous work is there!**
   - Objects
   - Tasks
   - Chat messages
   - Everything

---

## ⚙️ Configuration

### Change Save Frequency

Edit `.env` on your server:

```bash
# Save every 1 minute (more frequent)
SAVE_INTERVAL=60

# Save every 5 minutes (less frequent)
SAVE_INTERVAL=300
```

Restart:
```bash
docker-compose restart
```

### Change Backup Retention

Edit `.env`:

```bash
# Keep last 20 backups
MAX_BACKUPS=20

# Keep only 5 backups (save disk space)
MAX_BACKUPS=5
```

Restart:
```bash
docker-compose restart
```

---

## 📊 Monitoring

### Watch Auto-Saves

```bash
docker-compose logs -f | grep "Session saved"
```

You'll see messages every 2 minutes (or when users disconnect):
```
Session saved to disk (reason: auto-save)
Session saved to disk (reason: user_disconnect:Alice)
```

### Check Session Info

```bash
cat data/session_metadata.json
```

Shows:
- Last save timestamp
- Number of users
- Number of scene nodes
- Save reason

### Check Disk Usage

```bash
du -sh data/
ls -lh data/backups/
```

---

## 🔄 Recovery Examples

### Example 1: Planned Restart

```bash
# You restart for maintenance
docker-compose restart

# Server automatically:
# 1. Saves final snapshot
# 2. Restarts
# 3. Restores session

# Users reconnect → See all their work
```

**Result**: Zero data loss ✅

### Example 2: Server Crash

```bash
# Server crashes unexpectedly
# Last auto-save was 1.5 minutes ago

# You restart:
docker-compose up -d

# Server restores from last auto-save
# Lost: Only changes in last 1.5 minutes
```

**Result**: Minimal data loss ✅

### Example 3: User Disconnect

```bash
# User's Blender crashes
# Server detects disconnect → Saves immediately

# User reopens Blender → Reconnects
# All their work is there
```

**Result**: Work protected ✅

---

## 💾 Backup Management

### View Backups

```bash
# List all backups
ls -lh data/backups/

# Example output:
# snapshot_20250112_143025.pkl  (5.2 MB)
# snapshot_20250112_143225.pkl  (5.2 MB)
# snapshot_20250112_143425.pkl  (5.3 MB)
# ...
```

### Manual Backup

```bash
# Create manual backup
cp data/session_snapshot.pkl \
   data/manual_backup_$(date +%Y%m%d_%H%M%S).pkl
```

### Restore from Backup

```bash
# 1. Stop server
docker-compose down

# 2. Choose a backup
ls data/backups/

# 3. Restore it
cp data/backups/snapshot_20250112_120000.pkl \
   data/session_snapshot.pkl

# 4. Start server
docker-compose up -d
```

### External Backup (Recommended)

Set up daily backups to external storage:

```bash
# Add to crontab
crontab -e

# Add:
0 2 * * * rsync -av ~/blender-server/data/ /backup/location/$(date +\%Y\%m\%d)/
```

---

## 🐛 Troubleshooting

### Server Won't Start

```bash
# Check logs
docker-compose logs

# Common fix: rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### No Snapshots Being Created

**Check**:
```bash
# 1. Verify volume mount
docker inspect blender-multiuser-server | grep data

# 2. Check permissions
ls -la data/

# 3. Check logs for errors
docker-compose logs | grep "Failed to save"
```

**Fix**:
```bash
# Fix permissions
chmod 755 data/
docker-compose restart
```

### Session Not Restoring

**Check**:
```bash
# Verify snapshot exists
ls -lh data/session_snapshot.pkl

# Check logs
docker-compose logs | grep "restore"
```

**Fix**:
```bash
# If snapshot corrupted, use backup
docker-compose down
cp data/backups/snapshot_20250112_120000.pkl \
   data/session_snapshot.pkl
docker-compose up -d
```

---

## 📚 Documentation

After deployment, you have these guides on your server:

- **PERSISTENT_STORAGE.md** - Complete guide
- **UPGRADE_TO_PERSISTENT.md** - Detailed upgrade steps
- **README.md** - Updated server documentation

---

## 💡 Tips

### 1. Monitor First Few Days

```bash
# Watch logs
docker-compose logs -f

# Check saves are happening
docker-compose logs | grep "Session saved"

# Verify backups accumulating
ls -lh data/backups/
```

### 2. Test Recovery Early

Within first week:
```bash
docker-compose restart
docker-compose logs | grep "restored"
```

### 3. Set Up External Backups

For critical projects, backup `data/` directory daily.

### 4. Adjust Settings

Fine-tune based on your usage:
- Heavy editing → Lower `SAVE_INTERVAL` (60s)
- Stable sessions → Higher `SAVE_INTERVAL` (300s)
- Disk limited → Lower `MAX_BACKUPS` (5)
- Want history → Higher `MAX_BACKUPS` (20)

---

## ✅ Success Checklist

After deployment:

- [ ] Server running (`docker-compose ps`)
- [ ] Logs show "Auto-save enabled"
- [ ] `data/` directory exists
- [ ] After 2 min, `session_snapshot.pkl` created
- [ ] After user disconnect, new backup appears
- [ ] After restart, session restored
- [ ] Clients can connect and see previous work

---

## 🎉 You're Done!

Your server now has:
- ✅ Automatic session persistence
- ✅ Protection from data loss
- ✅ Automatic recovery
- ✅ Timestamped backups

**No more lost work from server restarts!**

---

## 🆘 Need Help?

1. Check logs: `docker-compose logs`
2. Read guides in `server/` directory
3. Verify setup with checklist above
4. Report issues with log output

---

**Updated**: January 12, 2025
**For**: Multi-User v0.8.1+
