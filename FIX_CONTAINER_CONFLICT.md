# Fix Container Conflict Error

## The Error You're Seeing

```
Error response from daemon: Conflict. The container name "/blender-multiuser-server" is already in use
```

This means the old container is still running and needs to be stopped first.

---

## Quick Fix

Run these commands on your server:

```bash
# Stop and remove the old container
docker stop blender-multiuser-server
docker rm blender-multiuser-server

# Or use docker-compose to clean up
docker-compose down

# Now you can start fresh
docker-compose up -d
```

---

## Complete Clean Deployment

If you want to be absolutely sure everything is clean:

```bash
# Stop and remove all related containers
docker-compose down

# Remove the container by name (if it still exists)
docker rm -f blender-multiuser-server 2>/dev/null || true

# Rebuild from scratch
docker-compose build --no-cache

# Start the new container
docker-compose up -d

# Check logs
docker-compose logs --tail 50
```

---

## Verify It's Fixed

After running the commands, check:

```bash
# Should show the container running
docker-compose ps

# Should show v2 banner
docker-compose logs | grep "Persistent Storage v2"
```

---

## About the Warning

The warning:
```
WARN[0000] /root/blender-server/docker-compose.yml: the attribute `version` is obsolete
```

This is just a warning, not an error. It's safe to ignore. If you want to fix it, remove line 1 from docker-compose.yml:

```yaml
# Remove this line:
version: '3.8'

# Keep the rest:
services:
  blender-collab-server:
    ...
```

But this is optional - the warning doesn't affect functionality.

---

## Summary

**Run this on your server:**

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
docker-compose logs --tail 50
```

That should fix the conflict and deploy v2 successfully!
