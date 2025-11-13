# Upgrade Guide: Adding Persistent Storage

This guide helps you upgrade your existing Multi-User server to include persistent storage.

---

## 🎯 What You Get

After this upgrade:
- ✅ Session data saved every 2 minutes automatically
- ✅ Data saved when users disconnect
- ✅ Automatic recovery after server restarts
- ✅ **No more data loss from restarts**

---

## 📋 Prerequisites

- Existing Multi-User server (any version)
- SSH access to your server
- Docker installed (for Docker deployments)

---

## 🚀 Upgrade Steps

### Step 1: Backup Current Setup

```bash
# SSH into your server
ssh user@your-server.com

# Backup current server directory
cd ~
tar -czf blender-server-backup-$(date +%Y%m%d).tar.gz blender-server/

# Verify backup
ls -lh blender-server-backup-*.tar.gz
```

### Step 2: Stop Current Server

```bash
cd ~/blender-server
docker-compose down
```

### Step 3: Update Server Files

**Option A: Via Git (if you use Git)**

```bash
cd ~/blender-server
git pull origin main
```

**Option B: Manual Upload**

From your local machine:

```bash
# Upload new files
scp server/persistent_server.py user@your-server.com:~/blender-server/
scp server/Dockerfile user@your-server.com:~/blender-server/
scp server/docker-compose.yml user@your-server.com:~/blender-server/
scp server/.env.example user@your-server.com:~/blender-server/
scp server/PERSISTENT_STORAGE.md user@your-server.com:~/blender-server/
```

### Step 4: Update Environment File

```bash
# On your server
cd ~/blender-server

# Add new variables to .env
cat >> .env << 'EOF'

# === Persistent Storage Settings ===
SAVE_INTERVAL=120
MAX_BACKUPS=10
EOF

# Verify .env file
cat .env
```

### Step 5: Rebuild Docker Container

```bash
# Rebuild with new persistent server
docker-compose build

# Verify build succeeded
docker-compose images
```

### Step 6: Start Upgraded Server

```bash
# Start server with persistent storage
docker-compose up -d

# Watch logs to verify it's working
docker-compose logs -f
```

Look for these log messages:
```
Multi-User Blender Server with Persistent Storage
Data Directory: /app/data
Auto-save Interval: 120 seconds
Max Backups: 10
Auto-save enabled (interval: 120s)
```

### Step 7: Verify Persistence

```bash
# Check data directory exists
ls -la ~/blender-server/data/

# Should see:
# drwxr-xr-x  backups/

# After first save (2 minutes), you'll see:
# -rw-r--r--  session_snapshot.pkl
# -rw-r--r--  session_metadata.json
```

---

## ✅ Verification Checklist

After upgrade, verify:

- [ ] Server starts without errors
- [ ] Clients can connect successfully
- [ ] `data/` directory exists in server folder
- [ ] Logs show "Auto-save enabled"
- [ ] After 2 minutes, `session_snapshot.pkl` appears
- [ ] After user disconnect, snapshot is updated
- [ ] After restart, session is restored

---

## 🧪 Testing Recovery

Test that recovery works:

```bash
# 1. Have users connect and make changes
# (wait for auto-save message in logs)

# 2. Note current session state
docker-compose logs | tail -20

# 3. Restart server
docker-compose restart

# 4. Check logs for restoration
docker-compose logs | grep restore

# Should see:
# "Session restored from disk"
# "Timestamp: 2025-01-12T14:32:25"
```

---

## ⚙️ Configuration

### Adjust Auto-Save Frequency

Edit `.env`:

```bash
# Save every 5 minutes instead of 2
SAVE_INTERVAL=300

# Save every 30 seconds (more frequent)
SAVE_INTERVAL=30
```

Then restart:
```bash
docker-compose restart
```

### Adjust Backup Retention

Edit `.env`:

```bash
# Keep last 20 backups instead of 10
MAX_BACKUPS=20

# Keep only 5 backups (less disk space)
MAX_BACKUPS=5
```

Then restart:
```bash
docker-compose restart
```

---

## 📊 Monitoring

### Watch Auto-Saves

```bash
# Live monitoring
docker-compose logs -f | grep "Session saved"

# Count saves today
docker-compose logs --since today | grep -c "Session saved"
```

### Check Disk Usage

```bash
# Check data directory size
du -sh ~/blender-server/data/

# Check individual snapshots
ls -lh ~/blender-server/data/backups/
```

### View Session Info

```bash
# View latest session metadata
cat ~/blender-server/data/session_metadata.json

# Pretty print
cat ~/blender-server/data/session_metadata.json | python -m json.tool
```

---

## 🔄 Rollback (If Needed)

If you need to rollback to the old version:

```bash
# Stop server
docker-compose down

# Restore backup
cd ~
tar -xzf blender-server-backup-YYYYMMDD.tar.gz

# Start old version
cd ~/blender-server
docker-compose up -d
```

---

## 🐛 Troubleshooting

### Issue: Container Won't Start

**Check logs**:
```bash
docker-compose logs
```

**Common fixes**:
```bash
# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Permission Errors on Data Directory

**Fix permissions**:
```bash
# On host
sudo chown -R 1000:1000 ~/blender-server/data/
chmod -R 755 ~/blender-server/data/
```

### Issue: Snapshots Not Being Created

**Check**:
1. Verify volume mount:
   ```bash
   docker inspect blender-multiuser-server | grep -A 5 Mounts
   ```

2. Check if users are connected:
   ```bash
   docker-compose logs | grep "User.*connected"
   ```

3. Verify SAVE_INTERVAL:
   ```bash
   docker-compose exec blender-collab-server env | grep SAVE
   ```

### Issue: Large Disk Usage

**Clean old backups**:
```bash
# Remove backups older than 7 days
find ~/blender-server/data/backups/ -name "*.pkl" -mtime +7 -delete

# Keep only last 5 backups
cd ~/blender-server/data/backups/
ls -t snapshot_*.pkl | tail -n +6 | xargs rm
```

**Reduce backup retention**:
```bash
# Edit .env
SAVE_INTERVAL=300  # 5 minutes
MAX_BACKUPS=5      # Keep only 5

# Restart
docker-compose restart
```

---

## 🔐 Security Notes

### Backup Security

Session snapshots contain all project data:
- Objects, materials, scenes
- Tasks and chat messages
- User information

**Recommendations**:
1. Restrict access to `data/` directory:
   ```bash
   chmod 700 ~/blender-server/data/
   ```

2. For sensitive projects, encrypt backups:
   ```bash
   # Encrypt data directory
   tar -czf - ~/blender-server/data | \
     openssl enc -aes-256-cbc -out data_backup_encrypted.tar.gz.enc
   ```

3. Store backups securely (e.g., encrypted S3 bucket)

---

## 📈 Performance Impact

After upgrade:
- **CPU**: < 1% additional (during saves)
- **Memory**: < 10 MB additional
- **Disk I/O**: Minimal (background writes)
- **Network**: Zero impact (saves are local)

Users won't notice any performance difference.

---

## 💡 Best Practices

### 1. Regular External Backups

Set up daily backups to external storage:

```bash
# Add to crontab
crontab -e

# Add line:
0 2 * * * rsync -av ~/blender-server/data/ /mnt/external/blender-backups/$(date +\%Y\%m\%d)/
```

### 2. Monitor Disk Space

Set up disk space monitoring:

```bash
# Check available space
df -h ~/blender-server/data/

# Alert if < 10% free
```

### 3. Test Recovery Monthly

Once per month, test that recovery works:
```bash
docker-compose restart
docker-compose logs | grep "restored"
```

---

## 🆘 Support

If you encounter issues:

1. **Check logs**:
   ```bash
   docker-compose logs --tail 100
   ```

2. **Verify configuration**:
   ```bash
   cat .env
   docker-compose config
   ```

3. **Check data directory**:
   ```bash
   ls -la ~/blender-server/data/
   cat ~/blender-server/data/session_metadata.json
   ```

4. **Report with details**:
   - Server OS and version
   - Docker version
   - Log output
   - .env configuration (hide passwords)

---

## ✅ Success!

You should now have:
- ✅ Server running with persistent storage
- ✅ Automatic saves every 2 minutes
- ✅ Backups being created
- ✅ Recovery working after restarts

Your session data is now safe from server restarts!

---

**Version**: 1.0
**Last Updated**: January 12, 2025
**For**: Multi-User v0.8.1+
