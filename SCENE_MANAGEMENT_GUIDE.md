# Scene Management User Guide

The Multi-User extension now has an improved, easy-to-use interface for managing multiple collaborative scenes.

## Quick Start

### 1. Connect to Server
First, connect to your Multi-User server as usual:
- Go to `Edit → Preferences → Multi-User`
- Select your server from the dropdown
- Click "Connect"

### 2. Access Scene Management
Once connected, open the **Multi-User** sidebar panel:
- In the 3D Viewport, press `N` to open the sidebar
- Click the **"Multi-User"** tab
- You'll see the **"Scenes"** panel

## Creating Scenes

### Create a Blank Scene
Perfect for starting fresh work:

1. In the **Scenes** panel, find the **"Create New Scene"** section
2. Click **"Create Blank Scene"** button
3. Enter a name for your scene (e.g., "Lighting Setup", "Animation Shot 1")
4. Click OK
5. **You're automatically switched to the new blank scene**

The new scene is immediately available to all connected users!

### Duplicate Current Scene
Perfect for variations or new shots based on existing work:

1. In the **Scenes** panel, find the **"Create New Scene"** section
2. Click **"Duplicate Current Scene"** button
3. Enter a name (default is "Current_Scene_Copy")
4. Click OK
5. **You're automatically switched to the duplicated scene**

The duplicate includes all objects, materials, and settings from the original scene.

## Switching Between Scenes

### View Available Scenes
In the **"Available Scenes"** section, you'll see:
- List of all scenes in the session
- Scene name
- Number of objects in each scene (e.g., "15 obj")

### Switch to a Scene
1. Find the scene you want in the **"Available Scenes"** list
2. Click the scene name button
3. **You instantly switch to that scene**

Each user can work in different scenes independently!

## Importing Objects Between Scenes

### Why Import Objects?
- Share assets between different scenes
- Reuse models, lights, or cameras
- Build asset libraries in one scene, use in others

### How to Import

**Step 1: Open Import Dialog**
1. Make sure you're in the scene where you want to import objects
2. In the **"Import Objects"** section, click **"Import from Other Scenes"** button
   - The button shows how many other scenes are available
   - Example: "Import from Other Scenes (2)"

**Step 2: Select Source Scene**
A popup appears showing all available scenes:
- Each scene shows its name and object count
- Example: "Lighting Setup (24 objects)"
- Click **"Select"** on the scene you want to import from

**Step 3: Choose Objects**
Another popup shows the import options:

**Option A: Import All Objects (Recommended)**
- Click the big **"Import All Objects (X)"** button at the top
- All objects from that scene are added to your current scene
- Fast and easy!

**Option B: Import Individual Objects**
- Scroll through the list of objects
- Each object shows its name and type (MESH, LIGHT, CAMERA, etc.)
- Click **"Import"** next to specific objects you want
- Perfect for selective importing

### Important Notes About Importing

✅ **Objects are linked, not copied**
- When you import an object, it's the same object across all scenes
- Edit it in one scene, changes appear everywhere
- This is great for shared assets like character models

✅ **Already imported objects are skipped**
- If an object is already in your scene, it won't be duplicated
- You'll see a message like "5 objects imported, 3 already present"

✅ **All users see the imported objects**
- When you import objects, all users in your scene see them appear
- Real-time synchronization

## Complete Workflow Example

### Scenario: Setting up a 3D animation project

**User A (Lead Artist):**
1. Connects to server
2. Creates blank scene: "Asset Library"
3. Models characters and props
4. Creates another blank scene: "Shot 01 - Kitchen"
5. Imports characters from "Asset Library" to "Shot 01 - Kitchen"
6. Sets up lighting and camera

**User B (Animator):**
1. Connects to same server
2. Sees both scenes: "Asset Library" and "Shot 01 - Kitchen"
3. Switches to "Shot 01 - Kitchen"
4. Starts animating the imported characters
5. Creates new scene: "Shot 02 - Living Room"
6. Imports same characters from "Asset Library"
7. Works on different animation

**User C (Lighting Artist):**
1. Connects to server
2. Switches to "Shot 01 - Kitchen"
3. Sees User B's animation in real-time
4. Adjusts lighting and materials
5. Creates scene: "Lighting Test"
6. Imports a character to test lighting setups
7. Once satisfied, applies lighting to main shots

**Result**: All three users work efficiently on different aspects of the project without conflicts!

## UI Overview

```
┌─────────────────────────────────────┐
│ Current Scene:                      │
│ • Shot 01 - Kitchen                 │
├─────────────────────────────────────┤
│ Create New Scene:                   │
│ [Create Blank Scene]                │
│ [Duplicate Current Scene]           │
├─────────────────────────────────────┤
│ Available Scenes:                   │
│ • Asset Library          15 obj     │
│ • Shot 02 - Living Room   8 obj     │
│ • Lighting Test           3 obj     │
├─────────────────────────────────────┤
│ Import Objects:                     │
│ [Import from Other Scenes (3)]      │
└─────────────────────────────────────┘
```

## Tips & Best Practices

### Organization
- **Use descriptive scene names** - "Shot_03_Chase" is better than "Scene.003"
- **Create an asset library scene** - Store reusable models, lights, materials
- **One scene per shot** - For animation projects, separate each camera shot
- **Separate setup scenes** - Create dedicated scenes for testing (lighting, materials, etc.)

### Collaboration
- **Communicate scene usage** - Let team know which scene you're working in
- **Don't delete scenes without asking** - Others might be using them
- **Use scene duplication for variations** - Test ideas in a copy before changing the main scene
- **Import liberally** - Share assets across scenes to maintain consistency

### Performance
- **Limit objects per scene** - Very large scenes (1000+ objects) may slow down sync
- **Use collections** - Organize objects in collections for easier management
- **Clean up unused scenes** - Delete test scenes when done to keep things tidy

### Asset Management
- **Single source of truth** - Keep master versions of models in the asset library scene
- **Update in place** - Edit imported objects to update them everywhere
- **Version with scene duplication** - Create "Asset_Library_v2" for major changes

## Troubleshooting

### "Scene already exists" error
- Each scene needs a unique name
- Try adding a number or description: "Kitchen_v2", "Kitchen_Final"

### Imported objects don't appear
- Make sure you're in Object mode (not Edit mode)
- Check if objects are on hidden collections
- Look in the outliner to verify objects are linked

### Can't see other user's scenes
- Both users must be connected to the same server
- Scene creation takes ~0.1 seconds to sync
- Try refreshing by switching scenes and back

### Objects imported multiple times
- This shouldn't happen - objects are only linked once
- If you see duplicates, they may be separate objects with similar names
- Check object names in the outliner

### Performance issues with many scenes
- Each scene adds overhead, but should be minimal
- Recommended: Keep under 10-15 scenes per session
- Delete unused scenes to improve performance

## Keyboard Shortcuts

Currently, scene management is done through the UI panel. However, you can:
- **Quick access**: Press `N` in 3D View to toggle the sidebar
- **Search**: Press `F3` and type "scene" to find scene operators
  - "Create Blank Scene"
  - "Duplicate Current Scene"
  - "Switch Scene"
  - "Import Objects"

## Related Features

- **Real-time sync** - All scene changes sync within 0.1 seconds
- **Keyframe sync** - Animations work across all scenes
- **Timeline sync** (optional) - Coordinate playback between users
- **Auto-updates** - Get notified of new features

## Advanced: Scene Data

### What Gets Synchronized?
When you create or switch scenes, these are synced:
- Scene settings (frame range, render settings)
- All objects in the scene
- Collections and hierarchy
- Animation data and keyframes
- Materials and textures
- World settings (background, lighting)

### What's NOT Shared Between Scenes?
- Camera view (each user can have different view)
- Object selection (each user selects independently)
- Timeline position (unless Timeline Sync is enabled)

## Support

Need help?
- Check the [main README](README.md) for general troubleshooting
- See [KEYFRAME_SYNC.md](KEYFRAME_SYNC.md) for animation-specific help
- Report issues on [GitHub](https://github.com/AvvyB/blender-multi-user/issues)

---

**Version**: 0.7.0
**Last Updated**: 2025-01-10

**Happy collaborating!** 🎨
