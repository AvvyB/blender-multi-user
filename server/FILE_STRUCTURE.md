# Internet Deployment - File Structure

## Overview

This document shows what was created to enable internet-based collaboration.

## Directory Structure

```
multi-user/
│
├── INTERNET_DEPLOYMENT.md          ← Main overview (START HERE!)
│
├── multi_user/                      ← Original addon (1 file modified)
│   ├── preferences.py               ← Added internet server preset
│   └── ...                          ← All other files unchanged
│
└── server/                          ← NEW! Server deployment package
    ├── README.md                    ← Complete deployment guide
    ├── CLIENT_SETUP.md              ← Client configuration guide
    ├── QUICK_REFERENCE.md           ← Quick reference card
    ├── FILE_STRUCTURE.md            ← This file
    │
    ├── docker-compose.yml           ← Docker Compose configuration
    ├── Dockerfile                   ← Docker image definition
    ├── .env.example                 ← Environment variables template
    │
    ├── deploy.sh                    ← Automated deployment script
    ├── standalone_server.py         ← Standalone Python server
    ├── requirements.txt             ← Python dependencies
    ├── blender-multiuser.service    ← Systemd service file
    │
    └── test_connection.py           ← Connection testing tool
```

## File Purposes

### Documentation (Read These!)

| File | Purpose | Who Reads It |
|------|---------|--------------|
| `INTERNET_DEPLOYMENT.md` | Main overview, start here | Everyone |
| `server/README.md` | Complete server deployment guide | Server admin |
| `server/CLIENT_SETUP.md` | Step-by-step client configuration | Blender users |
| `server/QUICK_REFERENCE.md` | Quick reference card | Everyone |
| `server/FILE_STRUCTURE.md` | This file - explains structure | Developers |

### Deployment Files (Use These!)

| File | Purpose | Deployment Method |
|------|---------|-------------------|
| `server/docker-compose.yml` | Docker orchestration | Docker |
| `server/Dockerfile` | Container definition | Docker |
| `server/.env.example` | Configuration template | All methods |
| `server/deploy.sh` | Automated deployment | Docker (automated) |
| `server/standalone_server.py` | Python server launcher | Python |
| `server/requirements.txt` | Python dependencies | Python |
| `server/blender-multiuser.service` | System service definition | Systemd |

### Tools (Run These!)

| File | Purpose | Usage |
|------|---------|-------|
| `server/test_connection.py` | Test server connectivity | `python test_connection.py IP PORT` |
| `server/deploy.sh` | Automated deployment | `./deploy.sh` |

### Modified Original Files

| File | Change | Reason |
|------|--------|--------|
| `multi_user/preferences.py` | Added internet server preset | Easier client configuration |

## What to Copy to Your Server

### Minimum (Docker Deployment)
```
server/
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── requirements.txt
```

### Recommended (Docker + Tools)
```
server/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
├── deploy.sh
├── test_connection.py
└── README.md
```

### Full Package (All Documentation)
```
entire server/ directory
```

## Usage Flow

### 1. Server Administrator

**First time:**
```bash
1. Read: INTERNET_DEPLOYMENT.md
2. Read: server/README.md
3. Copy: server/ → your cloud server
4. Run: ./deploy.sh
5. Save: passwords from output
```

**Ongoing:**
```bash
docker-compose logs    # Check logs
docker-compose restart # Restart server
docker-compose down    # Stop server
```

### 2. Blender Users (Clients)

**First time:**
```bash
1. Read: server/CLIENT_SETUP.md
2. Get: Server IP and passwords from admin
3. Configure: Blender → Preferences → Multi-User
4. Test: python test_connection.py SERVER_IP 5555
5. Connect: Multi-User panel → Join Session
```

**Ongoing:**
```bash
1. Open Blender
2. N → Multi-User → Join Session
3. Collaborate!
```

## Deployment Paths

### Path 1: Docker (Recommended)
```
.env.example → .env (configure)
       ↓
docker-compose.yml (defines services)
       ↓
Dockerfile (builds container)
       ↓
Server running on ports 5555-5557
```

### Path 2: Automated Docker
```
deploy.sh (runs everything)
    ↓
Installs Docker if needed
    ↓
Creates .env with secure passwords
    ↓
Configures firewall
    ↓
Starts server
```

### Path 3: Python Direct
```
requirements.txt → pip install
       ↓
standalone_server.py or python -m replication.server
       ↓
Server running
```

### Path 4: Systemd Service
```
blender-multiuser.service → /etc/systemd/system/
       ↓
systemctl enable blender-multiuser
       ↓
Server runs as system service
```

## Dependencies

### Server Dependencies
```
Python 3.10+
├── pyzmq (ZeroMQ Python bindings)
├── deepdiff (Delta synchronization)
├── orderly-set (Data structures)
└── replication (Core library)
    └── Located in: ../multi_user/wheels/replication-0.9.10-py3-none-any.whl
```

### Docker Dependencies
```
Docker 20.10+
└── Docker Compose 2.0+
```

### Client Dependencies
```
Blender 4.2+
└── Multi-User addon (this package)
    └── Already includes all dependencies in multi_user/wheels/
```

## Network Flow

```
Client (Blender)                     Server                      Other Clients
     │                                 │                              │
     │  TCP connect :5555              │                              │
     ├────────────────────────────────►│                              │
     │                                 │                              │
     │  Auth (username, password)      │                              │
     ├────────────────────────────────►│                              │
     │                                 │                              │
     │  Auth OK                        │                              │
     ◄────────────────────────────────┤                              │
     │                                 │                              │
     │  Request scene snapshot         │                              │
     ├────────────────────────────────►│                              │
     │                                 │                              │
     │  Scene data (port 5556)         │                              │
     ◄────────────────────────────────┤                              │
     │                                 │                              │
     │  Heartbeat (port 5557) ◄───────┼──────────────────────────────┤
     │                                 │                              │
     │  Object update                  │  Object update               │
     ├────────────────────────────────►├─────────────────────────────►│
     │                                 │                              │
     │  User position update           │  User position update        │
     ├────────────────────────────────►├─────────────────────────────►│
```

## Configuration Flow

```
Server Side:
.env file
  ├── ADMIN_PASSWORD ──┐
  ├── SERVER_PASSWORD ─┼──► Server validates clients
  └── PORT ───────────►     Opens TCP ports

Client Side:
Blender Preferences
  ├── Server IP ───────┐
  ├── Port ────────────┼──► Connects to server
  ├── Admin Password ──┤
  └── Server Password ─┘
```

## What Was Not Changed

### Unchanged Files
- All files in `multi_user/` except `preferences.py`
- Core collaboration logic
- Blender integration
- Data synchronization
- Ownership system
- UI panels and operators

### Unchanged Functionality
- Real-time editing
- User presence
- Object ownership
- Scene synchronization
- All Blender datablock types

**The only addition:** Ability to use it over the internet instead of just local network.

## Getting Started Checklist

### Server Admin
- [ ] Read `INTERNET_DEPLOYMENT.md`
- [ ] Read `server/README.md`
- [ ] Choose deployment method (Docker recommended)
- [ ] Copy server files to cloud server
- [ ] Run `./deploy.sh` or manual setup
- [ ] Note server IP and passwords
- [ ] Configure firewall (ports 5555-5557)
- [ ] Test with `test_connection.py`
- [ ] Share IP and passwords with team

### Blender User
- [ ] Get server IP and passwords from admin
- [ ] Read `server/CLIENT_SETUP.md`
- [ ] Open Blender → Preferences → Multi-User
- [ ] Configure internet server preset
- [ ] Test connection with `test_connection.py`
- [ ] Open Multi-User panel (N key)
- [ ] Select server and click "Join Session"
- [ ] Start collaborating!

## Summary

This package adds **one new directory** (`server/`) with **complete deployment infrastructure** and **modifies one line** in the original addon to add a convenient server preset.

The result: **Internet-based real-time Blender collaboration** without changing any core functionality.

---

**Questions?** See the appropriate documentation file above for your use case.
