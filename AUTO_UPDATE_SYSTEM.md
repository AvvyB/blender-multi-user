# Auto-Update System

## Overview

Multi-User includes an automatic update system that checks for new releases on GitHub and can install them with one click.

---

## How It Works

### Automatic Update Checking

- **Checks on startup**: Blender checks for updates 2 seconds after starting
- **Daily checks**: Updates checked once per day automatically
- **Manual checks**: Click "Check for Updates" button anytime

### Update Source

Updates are downloaded from:
- **GitHub Repository**: https://github.com/AvvyB/blender-multi-user
- **Releases page**: Uses GitHub Releases API
- **Direct downloads**: Downloads `.zip` files from releases

---

## User Experience

### When Update is Available

1. **Notification appears** in Multi-User panel
2. Shows new version number
3. Two buttons:
   - **Install Update** - One-click installation
   - **Dismiss** - Hide notification temporarily

### Installation Process

1. **Click "Install Update"**
2. **Progress shown**: Download progress bar
3. **Auto-install**: Removes old version, installs new version
4. **Restart prompt**: Popup asking to restart Blender
5. **Restart Blender** to use new version

### During Download

- Progress bar shows download percentage
- Status message: "Downloading Update..."
- Message: "Installing after download completes..."
- **Can't cancel** once started (safety measure)

---

## Technical Details

### Update Check Process

1. Fetches latest release from GitHub API:
   ```
   https://api.github.com/repos/AvvyB/blender-multi-user/releases/latest
   ```

2. Compares versions:
   - Installed: From `blender_manifest.toml`
   - Latest: From GitHub release tag (e.g., `v0.8.1`)

3. If newer version found:
   - Shows notification
   - Stores download URL for `.zip` asset

### Download Process

1. **Background download**: Uses Python `urllib.request.urlretrieve()`
2. **Progress tracking**: Updates shown in UI
3. **Temp storage**: Downloaded to temp directory
4. **Cleanup**: Temp files removed after installation

### Installation Process

1. **Remove old version**:
   ```python
   bpy.ops.preferences.extension_remove(module='multi_user')
   ```

2. **Install new version**:
   ```python
   bpy.ops.preferences.extension_install(filepath=zip_path)
   ```

3. **Clean up**: Delete temp files
4. **Prompt restart**: Show popup

---

## Configuration

### Update Check URL

In [multi_user/update_checker.py](multi_user/update_checker.py:32):

```python
GITHUB_RELEASES_API = "https://api.github.com/repos/AvvyB/blender-multi-user/releases/latest"
```

### Check Interval

```python
CHECK_INTERVAL_DAYS = 1  # Check once per day
```

To change:
- Edit `update_checker.py`
- Set `CHECK_INTERVAL_DAYS = 7` for weekly checks
- Set to `0` for always check on startup

---

## For Developers

### Creating a New Release

To trigger auto-updates for users:

1. **Update version** in `blender_manifest.toml`:
   ```toml
   version = "0.8.2"
   ```

2. **Build the package**:
   ```bash
   blender --command extension build --source-dir multi_user --output-dir .
   ```

3. **Create GitHub Release**:
   ```bash
   git tag v0.8.2
   git push origin v0.8.2
   ```

4. **Upload to GitHub**:
   - Go to: https://github.com/AvvyB/blender-multi-user/releases/new
   - Tag: `v0.8.2`
   - Title: `Multi-User v0.8.2`
   - Description: Changelog
   - **Attach**: `multi_user-0.8.2.zip` file
   - Publish release

5. **Users automatically notified** within 24 hours

### Asset Naming

The auto-updater looks for `.zip` files with "multi_user" in the name:

✅ **Works**:
- `multi_user-0.8.2.zip`
- `multi_user.zip`
- `blender-multi_user-0.8.2.zip`

❌ **Doesn't work**:
- `multiuser-0.8.2.zip` (missing underscore)
- `extension.zip` (no "multi_user")

### Version Format

Must use semantic versioning: `MAJOR.MINOR.PATCH`

✅ **Works**:
- `0.8.1`
- `1.0.0`
- `2.1.3`

❌ **Doesn't work**:
- `v0.8.1` (prefix handled automatically)
- `0.8` (needs patch number)
- `alpha-0.8.1` (no text)

---

## Troubleshooting

### Update Check Fails

**Symptoms**:
- No update notification appears
- Console shows "Update check failed"

**Causes**:
1. No internet connection
2. GitHub API rate limit (60 requests/hour)
3. GitHub is down

**Solutions**:
- Check internet connection
- Wait 1 hour if rate limited
- Check GitHub status: https://www.githubstatus.com
- Check manually: https://github.com/AvvyB/blender-multi-user/releases

### Download Fails

**Symptoms**:
- Error popup appears
- Console shows "Download failed"

**Causes**:
1. Internet connection lost during download
2. Release asset missing or wrong name
3. Insufficient disk space

**Solutions**:
- Check internet connection
- Verify release has `.zip` file with "multi_user" in name
- Check disk space (need ~10 MB free)
- Download manually from GitHub

### Installation Fails

**Symptoms**:
- Error popup: "Installation failed"
- Old version still installed

**Causes**:
1. Blender permissions issue
2. Extension directory locked
3. Corrupted download

**Solutions**:
1. **Try manual installation**:
   ```
   Edit → Preferences → Extensions → Install from Disk
   ```

2. **Check Blender has write permissions**:
   - Mac: System Preferences → Security → Privacy → Files and Folders
   - Windows: Run as Administrator
   - Linux: Check `~/.config/blender/` permissions

3. **Download fresh copy** from GitHub

### Update Doesn't Apply

**Symptoms**:
- Installation succeeded but still old version
- Didn't restart Blender

**Solution**:
**YOU MUST RESTART BLENDER** for updates to take effect!

---

## Security

### Download Verification

- Downloads only from GitHub releases
- Uses official GitHub API
- HTTPS only (encrypted)
- No external servers

### Installation Safety

- Uses Blender's official extension install API
- Removes old version first (clean install)
- Temp files cleaned up after install
- No system-wide changes

### Permissions

Requires:
- ✅ Network access (to download)
- ✅ File write access (to install)
- ❌ NO admin/root privileges
- ❌ NO access to other extensions

---

## FAQ

**Q: Do I have to update?**
A: No, updates are optional. You can dismiss notifications.

**Q: Can I turn off update checks?**
A: Not through UI, but you can edit `update_checker.py` and set `CHECK_INTERVAL_DAYS = 999999`.

**Q: What if I'm offline?**
A: Update checks fail silently. No errors shown.

**Q: Can I rollback to old version?**
A: Yes, download old release from GitHub and install manually.

**Q: Does it update the server?**
A: No, server updates are separate. This only updates the Blender extension.

**Q: How much data does it download?**
A: ~9 MB for the extension package.

**Q: Can I install without internet?**
A: Download `.zip` on another computer, then install from disk.

**Q: What if GitHub is down?**
A: Update checks will fail. Download manually when GitHub is back up.

**Q: Can multiple users update simultaneously?**
A: Yes, each Blender instance downloads independently.

**Q: Does it affect my work?**
A: No, installation happens in background. Restart required to use new version.

---

## Disabling Auto-Updates

If you want to disable automatic updates:

### Option 1: Increase Check Interval

Edit `multi_user/update_checker.py`:

```python
CHECK_INTERVAL_DAYS = 999999  # Effectively never check
```

Rebuild package.

### Option 2: Remove Update Handler

Edit `multi_user/update_checker.py`:

Comment out startup handler registration:

```python
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # DON'T register startup handler
    # if check_updates_on_startup not in bpy.app.handlers.load_post:
    #     bpy.app.handlers.load_post.append(check_updates_on_startup)
```

### Option 3: Dismiss Permanently

Click "Dismiss" on update notification. Won't show again until next version is released.

---

## For Network Administrators

### Firewall Rules

Auto-updates require access to:
- `api.github.com` (HTTPS/443) - Check for updates
- `github.com` (HTTPS/443) - Download releases
- `objects.githubusercontent.com` (HTTPS/443) - Asset downloads

To block updates:
- Block `api.github.com/repos/AvvyB/blender-multi-user`
- Users can still install manually

### Proxy Support

Updates use Python's `urllib`, which respects:
- `HTTP_PROXY` environment variable
- `HTTPS_PROXY` environment variable

Set in Blender startup:
```bash
export HTTPS_PROXY=http://proxy.company.com:8080
blender
```

---

## Monitoring

### Check Update System Status

In Blender console:

```python
from multi_user.update_checker import update_checker

# Check if update available
print(f"Update available: {update_checker.update_available}")
print(f"Latest version: {update_checker.latest_version}")
print(f"Download URL: {update_checker.download_url}")

# Force check now
update_checker.check_for_updates()
```

### View Logs

Enable debug logging in preferences:
- Log level: DEBUG
- Console shows update check messages

```
Update check: Installed=(0, 8, 1), Latest=(0, 8, 2), Available=True
Download URL: https://github.com/AvvyB/blender-multi-user/releases/download/v0.8.2/multi_user-0.8.2.zip
```

---

## Advanced: Custom Update Source

To use a different GitHub repository:

Edit `multi_user/update_checker.py`:

```python
# Change to your fork
GITHUB_RELEASES_API = "https://api.github.com/repos/YourUsername/your-repo/releases/latest"
```

Rebuild and distribute your custom version.

---

**Version**: 1.0
**Last Updated**: January 12, 2025
**For**: Multi-User v0.8.1+
