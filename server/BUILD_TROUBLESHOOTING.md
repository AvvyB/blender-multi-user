# Docker Build Troubleshooting

## Error: "standalone_server.py: not found"

This error means Docker can't find the required files during build.

---

## ✅ Solution

### The Issue

You're likely running `docker-compose build` from the **wrong directory**.

### The Fix

Make sure you're in the `server/` directory:

```bash
# SSH to your server
ssh user@your-server.com

# Navigate to the server directory
cd ~/blender-server

# Verify you're in the right place
pwd
# Should show: /home/user/blender-server

# List files to verify
ls -la

# You should see:
# - Dockerfile
# - docker-compose.yml
# - standalone_server.py
# - persistent_server.py
# - replication-0.9.10-py3-none-any.whl
# - requirements.txt

# NOW run the build
docker-compose build
```

---

## 🔍 Diagnostic Steps

### Step 1: Verify Directory

```bash
# Check current directory
pwd

# List files
ls -1

# You MUST see these files:
# Dockerfile
# docker-compose.yml
# standalone_server.py
# persistent_server.py
# replication-0.9.10-py3-none-any.whl
# requirements.txt
```

### Step 2: Verify Files Exist

```bash
# Check each required file
ls -lh Dockerfile
ls -lh docker-compose.yml
ls -lh standalone_server.py
ls -lh persistent_server.py
ls -lh replication-0.9.10-py3-none-any.whl
ls -lh requirements.txt

# All should show file sizes, not "No such file"
```

### Step 3: Check File Permissions

```bash
# Ensure files are readable
chmod 644 Dockerfile docker-compose.yml standalone_server.py persistent_server.py requirements.txt
chmod 644 replication-0.9.10-py3-none-any.whl
```

### Step 4: Try Build Again

```bash
# Clean old build cache
docker-compose down
docker system prune -f

# Build fresh
docker-compose build --no-cache
```

---

## 🚨 Common Mistakes

### ❌ Wrong: Running from parent directory

```bash
# DON'T DO THIS
cd ~/
docker-compose -f blender-server/docker-compose.yml build
# ❌ This won't work because the build context is wrong
```

### ✅ Correct: Running from server directory

```bash
# DO THIS
cd ~/blender-server
docker-compose build
# ✅ This works because build context is correct
```

---

## 🔧 Alternative: Specify Build Context

If you must run from parent directory:

Edit `docker-compose.yml` to specify build context:

```yaml
services:
  blender-collab-server:
    build:
      context: .          # Current directory (server/)
      dockerfile: Dockerfile
```

Then:
```bash
cd ~/blender-server
docker-compose build
```

---

## 📋 Complete Clean Build Process

If nothing else works, do a complete clean build:

```bash
# 1. Stop and remove everything
docker-compose down
docker system prune -a -f

# 2. Verify files
cd ~/blender-server
ls -la | grep -E "(Dockerfile|standalone|persistent|replication|requirements)"

# 3. Check Dockerfile content
head -20 Dockerfile

# 4. Build with verbose output
docker-compose build --progress=plain --no-cache 2>&1 | tee build.log

# 5. If it fails, check the log
less build.log
```

---

## 🔍 Debugging the Build

### See What Docker Sees

```bash
# Test what files Docker can access
docker run --rm -v "$(pwd):/test" alpine ls -la /test

# Should show all your server files including:
# - standalone_server.py
# - persistent_server.py
# - etc.
```

### Check Docker Daemon

```bash
# Ensure Docker is running
docker ps

# Check Docker version
docker --version
docker-compose --version
```

---

## 📝 Manual Build Test

If docker-compose fails, try manual docker build:

```bash
# From server directory
cd ~/blender-server

# Manual build
docker build -t blender-multiuser-test .

# If this works but docker-compose doesn't,
# there's an issue with docker-compose.yml
```

---

## 🛠️ File Upload Checklist

If files are missing, re-upload them:

```bash
# From your LOCAL machine
cd /Users/Avdon/Projects/multi-user

# Upload all server files
scp server/Dockerfile user@your-server.com:~/blender-server/
scp server/docker-compose.yml user@your-server.com:~/blender-server/
scp server/standalone_server.py user@your-server.com:~/blender-server/
scp server/persistent_server.py user@your-server.com:~/blender-server/
scp server/requirements.txt user@your-server.com:~/blender-server/
scp server/replication-0.9.10-py3-none-any.whl user@your-server.com:~/blender-server/
scp server/.env.example user@your-server.com:~/blender-server/

# Verify upload
ssh user@your-server.com "ls -la ~/blender-server/"
```

---

## 🔄 Fresh Start

If completely stuck, start fresh:

```bash
# On server
cd ~
rm -rf blender-server-old
mv blender-server blender-server-old

# On local machine
scp -r server/ user@your-server.com:~/blender-server/

# On server
cd ~/blender-server
cp blender-server-old/.env .  # Copy your passwords
docker-compose build
```

---

## ✅ Success Indicators

You know it's working when you see:

```
Building blender-collab-server
[+] Building 45.2s (12/12) FINISHED
 => [1/6] FROM docker.io/library/python:3.11-slim
 => [2/6] COPY requirements.txt .
 => [3/6] RUN pip install --no-cache-dir -r requirements.txt
 => [4/6] COPY replication-0.9.10-py3-none-any.whl .
 => [5/6] COPY standalone_server.py .
 => [6/6] COPY persistent_server.py .
Successfully built abc123def456
Successfully tagged server_blender-collab-server:latest
```

---

## 🆘 Still Not Working?

### Collect Diagnostics

```bash
# Run this on your server and share the output:

cd ~/blender-server

echo "=== Current Directory ==="
pwd

echo -e "\n=== Files Present ==="
ls -la

echo -e "\n=== Dockerfile Content ==="
head -20 Dockerfile

echo -e "\n=== Docker Version ==="
docker --version
docker-compose --version

echo -e "\n=== Build Attempt ==="
docker-compose build 2>&1 | head -50

echo -e "\n=== Docker System Info ==="
docker info | head -20
```

Save output to a file:
```bash
cd ~/blender-server
./diagnostics.sh > build_diagnostics.txt 2>&1
cat build_diagnostics.txt
```

---

## 💡 Quick Fix Commands

Try these in order:

```bash
# Fix 1: Ensure in correct directory
cd ~/blender-server && docker-compose build

# Fix 2: Clean build
cd ~/blender-server && docker-compose build --no-cache

# Fix 3: Prune and rebuild
cd ~/blender-server && docker system prune -f && docker-compose build

# Fix 4: Manual build
cd ~/blender-server && docker build -t test .

# Fix 5: Check file permissions
cd ~/blender-server && chmod 644 *.py *.txt *.whl Dockerfile && docker-compose build
```

---

**Version**: 1.0
**Last Updated**: January 12, 2025
