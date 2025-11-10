# Auto-Update System Setup Guide

The Multi-User extension now includes an automatic update notification system that alerts users when new versions are available.

## How It Works

1. **On Blender startup**: Extension checks for updates (once per day)
2. **If update found**: Shows notification in preferences
3. **User clicks "Download"**: Opens browser to latest release
4. **Manual check**: Button in preferences to check anytime

## Setup Instructions

### Step 1: Host version.json File

You need to host the `version.json` file somewhere publicly accessible. Here are your options:

#### Option A: GitHub (Recommended)

1. **Create a GitHub repository** for the extension (if you don't have one):
   ```bash
   cd /Users/Avdon/Projects/multi-user
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/multi-user.git
   git push -u origin main
   ```

2. **Upload version.json** to the root of the repository

3. **Get the raw URL**:
   ```
   https://raw.githubusercontent.com/YOUR_USERNAME/multi-user/main/version.json
   ```

4. **Update the URL in update_checker.py** (line 28):
   ```python
   UPDATE_CHECK_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/multi-user/main/version.json"
   ```

#### Option B: Your Own Server

1. **Upload version.json** to your web server:
   ```bash
   scp version.json user@your-server.com:/var/www/html/multi-user/
   ```

2. **Update the URL in update_checker.py**:
   ```python
   UPDATE_CHECK_URL = "https://your-server.com/multi-user/version.json"
   ```

#### Option C: GitHub Gist

1. Create a new gist at https://gist.github.com
2. Name the file `version.json`
3. Paste the content
4. Click "Create public gist"
5. Click "Raw" button and copy the URL
6. Update `UPDATE_CHECK_URL` in update_checker.py

### Step 2: Update version.json for Each Release

When you release a new version:

1. **Edit version.json**:
   ```json
   {
     "version": "0.7.0",
     "release_date": "2025-01-15",
     "download_url": "https://github.com/YOUR_USERNAME/multi-user/releases/download/v0.7.0/multi_user-0.7.0.zip",
     "release_notes": "Brief description of changes",
     "min_blender_version": "4.3.0",
     "changelog": [
       "Feature 1",
       "Feature 2",
       "Bug fix 3"
     ]
   }
   ```

2. **Update the version number**:
   - Increment version in `blender_manifest.toml`
   - Update version in `version.json`
   - Both must match!

3. **Commit and push**:
   ```bash
   git add version.json multi_user/blender_manifest.toml
   git commit -m "Release v0.7.0"
   git tag v0.7.0
   git push origin main --tags
   ```

4. **Create GitHub Release**:
   - Go to your repo → Releases → New Release
   - Tag: v0.7.0
   - Upload: `multi_user-0.7.0.zip`
   - Publish

### Step 3: Rebuild Extension with Your URL

1. **Edit multi_user/update_checker.py** (line 28):
   ```python
   UPDATE_CHECK_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/multi-user/main/version.json"
   ```

2. **Rebuild the zip**:
   ```bash
   cd /Users/Avdon/Projects/multi-user
   rm -f multi_user-0.6.9.zip
   zip -r multi_user-0.6.9.zip multi_user/ -x "*.git*" "*__pycache__*" "*.pyc"
   ```

3. **Distribute this version** to users

## version.json Schema

```json
{
  "version": "0.6.9",              // Semantic version (REQUIRED)
  "release_date": "2025-01-09",    // ISO date format (optional)
  "download_url": "https://...",   // Direct download link (optional)
  "release_notes": "Summary",      // Brief description (optional)
  "min_blender_version": "4.3.0",  // Minimum Blender version (optional)
  "changelog": [                   // List of changes (optional)
    "Change 1",
    "Change 2"
  ]
}
```

**Only `version` is required.** Everything else is optional.

## User Experience

### First-Time Setup (User Side)

1. User installs `multi_user-0.6.9.zip`
2. Restarts Blender
3. After 2 seconds, extension checks for updates
4. If update available, shows notification

### When Update Available

**In Preferences** (Edit → Preferences → Multi-User):
```
┌─────────────────────────────────────┐
│ ⚠ Update Available: v0.7.0         │
│ [ Download ] [ Dismiss ]            │
└─────────────────────────────────────┘
```

**Click "Download"**:
- Opens browser to GitHub releases page
- User downloads new zip
- User removes old extension
- User installs new extension
- Done!

### Manual Check

User can click "Check for Updates" button anytime in preferences.

## Update Flow Diagram

```
Blender Starts
    ↓
Wait 2 seconds
    ↓
Check last update time
    ↓
If > 24 hours ago → Fetch version.json
    ↓                       ↓
    ↓                   Parse version
    ↓                       ↓
    ↓               Compare with installed
    ↓                       ↓
    ↓              If newer → Show notification
    ↓                       ↓
User sees update notification
    ↓
Clicks "Download"
    ↓
Browser opens to releases page
    ↓
User downloads and installs
```

## Configuration Options

### Check Frequency

Edit `multi_user/update_checker.py` (line 29):
```python
CHECK_INTERVAL_DAYS = 1  # Check daily (default)
CHECK_INTERVAL_DAYS = 7  # Check weekly
CHECK_INTERVAL_DAYS = 0  # Check every Blender start (not recommended)
```

### Disable Auto-Check

To disable automatic checking, comment out the startup handler:

```python
# In multi_user/update_checker.py register() function:
# Don't register the startup handler
# if check_updates_on_startup not in bpy.app.handlers.load_post:
#     bpy.app.handlers.load_post.append(check_updates_on_startup)
```

Users can still manually check with the button.

## Testing

### Test Update Notification

1. **Temporarily change installed version**:
   Edit `multi_user/blender_manifest.toml`:
   ```toml
   version = "0.1.0"  # Old version
   ```

2. **Update version.json**:
   ```json
   {"version": "0.6.9"}
   ```

3. **Restart Blender**

4. **Check preferences** → Should show update notification

5. **Restore real version** after testing

### Test URL Fetch

```bash
curl https://raw.githubusercontent.com/YOUR_USERNAME/multi-user/main/version.json
```

Should return valid JSON.

## Troubleshooting

### Update notification not showing?

1. **Check Blender console** (Window → Toggle System Console):
   ```
   Update check: Installed=(0,6,9), Latest=(0,7,0), Available=True
   ```

2. **Verify version.json is accessible**:
   - Open URL in browser
   - Should see JSON content

3. **Check update interval**:
   - Only checks once per day
   - Delete last check time to force recheck

### Users not getting notifications?

1. **Verify they have internet access**
2. **Check firewall isn't blocking Python**
3. **Ensure UPDATE_CHECK_URL is correct**

### Wrong version showing?

1. **Clear Blender's extension cache**
2. **Reinstall extension**
3. **Verify blender_manifest.toml version matches**

## Privacy & Security

### What Data is Sent?

**None!** The extension only:
- Makes a GET request to version.json URL
- No user data is transmitted
- No tracking or analytics

### Is it secure?

- Uses HTTPS (if you use GitHub/HTTPS server)
- Read-only operation
- No code execution from remote
- User must manually download updates

## Best Practices

### Version Numbering

Follow semantic versioning:
- `MAJOR.MINOR.PATCH`
- `0.6.9` → `0.6.10` (bug fix)
- `0.6.9` → `0.7.0` (new feature)
- `0.6.9` → `1.0.0` (major changes)

### Release Process

1. Update code
2. Update `blender_manifest.toml` version
3. Update `version.json` version and changelog
4. Git commit and tag
5. Build zip file
6. Create GitHub release
7. Upload zip to release
8. Update download_url in version.json
9. Announce to users

### Changelog Writing

Good:
```json
"changelog": [
  "Added internet server support",
  "Fixed timeline sync crashes",
  "Improved update rate to 0.1s"
]
```

Bad:
```json
"changelog": [
  "Bug fixes",
  "Performance improvements"
]
```

## Example GitHub Workflow

### Initial Setup

```bash
# 1. Create repo
git init
git add .
git commit -m "v0.6.9 - Initial release"

# 2. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/multi-user.git
git push -u origin main

# 3. Create first release
git tag v0.6.9
git push origin v0.6.9

# 4. Upload zip on GitHub releases page
```

### Future Updates

```bash
# 1. Make changes
# ... edit code ...

# 2. Update versions
# Edit: multi_user/blender_manifest.toml → version = "0.7.0"
# Edit: version.json → version = "0.7.0"

# 3. Commit
git add .
git commit -m "v0.7.0 - New features"
git tag v0.7.0
git push origin main --tags

# 4. Build
rm multi_user-0.7.0.zip
zip -r multi_user-0.7.0.zip multi_user/ -x "*.git*"

# 5. Create release on GitHub
# Upload multi_user-0.7.0.zip
```

## Alternative: Blender Extensions Platform

When the official Blender Extensions platform launches, you can:
1. Submit extension there
2. Users get automatic updates through Blender
3. No need for manual update system

But until then, this system works great!

---

## Quick Reference

**Files to Update:**
- `multi_user/blender_manifest.toml` - version number
- `version.json` - version, changelog, download URL
- `multi_user/update_checker.py` - UPDATE_CHECK_URL (once)

**Release Checklist:**
- [ ] Update version in blender_manifest.toml
- [ ] Update version.json
- [ ] Commit and tag
- [ ] Build zip file
- [ ] Create GitHub release
- [ ] Upload zip
- [ ] Update download_url in version.json
- [ ] Announce!

**User Notification:**
```
Users will automatically be notified within 24 hours after you:
1. Update version.json on GitHub
2. Set version higher than their installed version
```

That's it! The auto-update system is ready to use. 🚀
