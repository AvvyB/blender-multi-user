# MULTI-USER for Blender - Internet Edition

> Real-time collaborative workflow for Blender across the internet

<img src="https://i.imgur.com/X0B7O1Q.gif" width=600>

This extension enables multiple users to work on the same Blender scene in real-time over the internet. Built on a centralized Client/Server architecture using ZeroMQ over TCP, it synchronizes Blender data-blocks across the network with minimal latency.

## Key Features

- **Internet Collaboration** - Work with teams across the globe, not just local networks
- **Real-time Synchronization** - 10x faster updates (0.1s default) for smooth collaboration
- **Keyframe & Animation Sync** - Automatic synchronization of animations and keyframes
- **Optional Timeline Sync** - Synchronized playback across all users
- **Auto-Update Notifications** - Get notified when new versions are available
- **Ownership System** - Prevents editing conflicts with intelligent object ownership
- **Blender 4.3+ Compatible** - Works with the latest Blender extension system

## Quick Installation

### For Users (Client Setup)

1. **Download the latest release**:
   - Visit [GitHub Releases](https://github.com/AvvyB/blender-multi-user/releases/latest)
   - Download `multi_user-X.X.X.zip`

2. **Install in Blender**:
   - Open Blender 4.3 or later
   - Go to `Edit → Preferences → Extensions`
   - Click the dropdown arrow at the top-right
   - Select `Install from Disk...`
   - Choose the downloaded ZIP file
   - Enable the "Multi-User" extension

3. **Configure connection**:
   - In Preferences → Multi-User
   - Select "Internet Server" preset
   - Enter your server's IP address and port
   - Save preferences

For detailed setup instructions, see [CLIENT_SETUP.md](server/CLIENT_SETUP.md).

### For Server Administrators

**Deploy your own collaboration server using Docker:**

1. **Prerequisites**:
   - Docker and Docker Compose installed
   - Public IP address or domain name
   - Ports 5555-5557 accessible

2. **Quick deployment**:
   ```bash
   cd server/
   ./prepare.sh
   # Edit .env with your configuration
   ./deploy.sh
   ```

For complete deployment instructions, see [server/README.md](server/README.md).

## How It Works

### Architecture

```
Client 1 (Blender) ←→ Server (ZeroMQ) ←→ Client 2 (Blender)
                          ↕
                    Client 3 (Blender)
```

- **Centralized Server**: Routes all updates between clients
- **Delta-based Sync**: Only changed data is transmitted
- **Three-port System**:
  - Port 5555: Command channel (room management)
  - Port 5556: Data channel (scene synchronization)
  - Port 5557: Heartbeat channel (connection monitoring)

### Synchronization Features

#### Object & Scene Data
- **Real-time updates**: Changes sync within 0.1 seconds
- **Ownership system**: Selected objects are owned by the user
- **Automatic detection**: Blender's dependency graph triggers updates

#### Keyframes & Animation
- **Automatic sync**: Keyframes visible to all users
- **Action sharing**: Animation data automatically replicated
- **Editable**: All users can modify keyframes

#### Timeline Playback (Optional)
- **Synchronized playback**: All users follow the same timeline
- **Leader/follower system**: First user alphabetically controls playback
- **Opt-in**: Disabled by default to prevent conflicts

### Update Notifications

The extension automatically checks for updates on Blender startup (once per day):
- Shows notification in preferences when updates are available
- One-click download to latest release
- Manual check available anytime

For setup instructions, see [AUTO_UPDATE_SETUP.md](AUTO_UPDATE_SETUP.md).

## Supported Data-Blocks

| Data-block     | Status |                                 Comment                                 |
| -------------- | :----: | :---------------------------------------------------------------------: |
| action         |   ✔️    | Fully synchronized with automatic keyframe sharing                      |
| camera         |   ✔️    |                                                                         |
| collection     |   ✔️    |                                                                         |
| gpencil        |   ✔️    |                                                                         |
| gpencil3       |   ✔️    |                                                                         |
| image          |   ✔️    |                                                                         |
| mesh           |   ✔️    |                                                                         |
| material       |   ✔️    |                                                                         |
| node_groups    |   ✔️    | Material & Geometry only                                                |
| geometry nodes |   ✔️    |                                                                         |
| metaball       |   ✔️    |                                                                         |
| object         |   ✔️    |                                                                         |
| texts          |   ✔️    |                                                                         |
| scene          |   ✔️    |                                                                         |
| world          |   ✔️    |                                                                         |
| volumes        |   ✔️    |                                                                         |
| lightprobes    |   ✔️    |                                                                         |
| physics        |   ✔️    |                                                                         |
| textures       |   ✔️    |                                                                         |
| curve          |   ❗    | Nurbs surfaces not supported                                            |
| armature       |   ❗    | Only for Mesh. Not stable yet                                           |
| particles      |   ❗    | The cache isn't syncing                                                 |
| speakers       |   ❗    | Partial support                                                         |
| vse            |   ❗    | Mask and Clip not supported yet                                         |
| libraries      |   ❌    |                                                                         |
| nla            |   ❌    |                                                                         |
| compositing    |   ❌    |                                                                         |

## Configuration

### Connection Presets

The extension includes built-in presets:

- **Localhost** - For testing on the same machine
- **LAN Server** - For local network collaboration
- **Internet Server** - For global collaboration (configure with your server IP)

### Performance Settings

- **Update Rate**: Adjustable from 0.05s to 2.0s (default: 0.1s)
- **Timeline Sync**: Optional synchronized playback
- **Auto-connect**: Reconnect automatically on Blender startup

### Server Configuration

Environment variables for server deployment:

```bash
SERVER_IP=0.0.0.0
COMMAND_PORT=5555
DATA_PORT=5556
HEARTBEAT_PORT=5557
UPDATE_RATE=0.1
ROOM_NAME=default
PASSWORD=your_secure_password
```

## Documentation

- **[Server Deployment Guide](server/README.md)** - Complete server setup with Docker
- **[Client Setup Guide](server/CLIENT_SETUP.md)** - Step-by-step client configuration
- **[Auto-Update Setup](AUTO_UPDATE_SETUP.md)** - Configure update notifications
- **[Quick Reference](server/QUICK_REFERENCE.md)** - Common commands and troubleshooting

## Troubleshooting

### Connection Issues

**Problem**: "Server was lost" immediately after connecting
- **Solution**: Check firewall rules allow ports 5555-5557
- **Solution**: Verify server is running with `docker ps`
- **Solution**: Test connection with `python server/test_connection.py`

**Problem**: "Failed to connect to server"
- **Solution**: Verify server IP/domain is correct
- **Solution**: Check server logs: `docker logs blender-collab-server`
- **Solution**: Ensure ports are publicly accessible (not blocked by cloud provider)

### Synchronization Issues

**Problem**: Changes not appearing on other clients
- **Solution**: Check both clients are in the same room
- **Solution**: Verify update rate isn't set too high
- **Solution**: Check Blender console for error messages

**Problem**: Timeline fighting between users
- **Solution**: Ensure only one user has Timeline Sync enabled
- **Solution**: Leader is determined alphabetically (first user controls)

### Performance Issues

**Problem**: Lag or delay in updates
- **Solution**: Lower update rate (0.05s for faster sync)
- **Solution**: Check network latency between client and server
- **Solution**: Reduce scene complexity (fewer objects = faster sync)

For more help, check the [Blender console](Window → Toggle System Console) for detailed error messages.

## Performance Notes

This extension is optimized for real-time collaboration:

- **10x faster** than original version (0.1s default vs 1.0s)
- **Delta-based sync** - Only changed data transmitted
- **Efficient protocol** - ZeroMQ's zero-copy messaging
- **Background threads** - Non-blocking update checks

Since the extension is written in pure Python, there are inherent performance limits. For large scenes with many objects, consider:
- Increasing update rate to 0.2s or 0.5s
- Disabling timeline sync if not needed
- Working in separate collections to reduce conflicts

## Dependencies

| Dependency    | Version | Required | Notes                              |
| ------------- | :-----: | :------: | ---------------------------------- |
| Replication   | 0.9.10  | Yes      | Bundled with extension             |
| PyZMQ         | 26.2.1  | Yes      | Bundled with extension             |
| DeepDiff      | 8.1.1   | Yes      | Bundled with extension             |
| Python        | 3.11+   | Yes      | Included with Blender 4.3+         |

All dependencies are automatically installed during extension installation.

## Version Compatibility

- **Blender**: 4.3.0 or later (uses new extension system)
- **Python**: 3.11+ (included with Blender 4.3+)
- **OS**: Windows, macOS, Linux

For Blender 4.2, see the [legacy branch](https://github.com/AvvyB/blender-multi-user/tree/blender-4.2).

## Cloud Deployment

Deploy your server on popular cloud providers:

### DigitalOcean
```bash
# Create droplet (Ubuntu 24.04)
# SSH into server
git clone https://github.com/AvvyB/blender-multi-user.git
cd blender-multi-user/server
./prepare.sh
# Edit .env with your public IP
./deploy.sh
```

### AWS EC2
- Launch Ubuntu 24.04 instance (t2.micro sufficient for small teams)
- Open ports 5555-5557 in Security Group
- Follow DigitalOcean instructions above

### Google Cloud Platform
- Create Compute Engine instance (e2-micro sufficient)
- Configure firewall rules for ports 5555-5557
- Follow DigitalOcean instructions above

See [server/README.md](server/README.md) for detailed cloud deployment examples.

## Security Considerations

### Network Security
- **Password protection**: Set strong passwords in server configuration
- **Firewall rules**: Only open required ports (5555-5557)
- **HTTPS**: Consider reverse proxy with SSL/TLS for production

### Data Privacy
- **No telemetry**: Extension doesn't send usage data
- **Local updates**: Auto-update only checks version number
- **No account required**: Simple password-based authentication

### Best Practices
- Use strong passwords (16+ characters)
- Restrict server access to known IPs when possible
- Regularly update to latest version
- Monitor server logs for unauthorized access attempts

## Contributing

Contributions are welcome! This project builds upon the excellent work of the original multi-user addon.

**Areas for contribution**:
- Additional data-block support (NLA, compositing, etc.)
- Performance optimizations
- Documentation improvements
- Bug fixes and testing

**How to contribute**:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For questions or discussions, open an issue on [GitHub](https://github.com/AvvyB/blender-multi-user/issues).

## Roadmap

### Version 0.7.0 (Planned)
- [ ] Compositing node support
- [ ] NLA editor synchronization
- [ ] Improved armature stability
- [ ] Server-side room management UI
- [ ] WebSocket support for web-based monitoring

### Version 0.8.0 (Future)
- [ ] Voice chat integration
- [ ] Cursor/viewport sharing
- [ ] Session recording and playback
- [ ] Advanced permissions system

## Credits

This extension is based on the original [multi-user addon](https://gitlab.com/slumber/multi-user) by the Slumber team. Enhanced with internet collaboration, performance improvements, and modern Blender compatibility.

**Original Authors**: Slumber team and contributors
**Internet Edition**: AvvyB and contributors

Special thanks to the Blender community and all contributors who made this project possible.

## Licensing

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [LICENSE](LICENSE) for full details.

## Support

- **Issues**: [GitHub Issues](https://github.com/AvvyB/blender-multi-user/issues)
- **Documentation**: See docs folder and markdown files
- **Updates**: Watch releases for new features and fixes

---

**Ready to collaborate?** Deploy your server and start creating together!
