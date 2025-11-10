# Keyframe Synchronization Guide

The Multi-User extension now has enhanced keyframe synchronization to ensure all users can see and edit each other's keyframes in real-time.

## How It Works

### 1. Action Datablock Sharing

Keyframes in Blender are stored in **Action** datablocks. When you insert a keyframe (by pressing `I` or using auto-key), Blender creates or modifies an Action attached to the object's animation data.

The extension synchronizes Actions across all users with these key features:

- **`bl_check_common = True`** - Actions are marked as "common" data, meaning they can be edited by any user (not just the owner)
- **Automatic detection** - When you modify an object with keyframes, the extension detects the change and syncs the associated Action
- **Real-time updates** - Changes propagate to all users within 0.1 seconds (default update rate)

### 2. Synchronization Flow

```
User adds keyframe → Object updates → Depsgraph detects change →
Handler finds associated Action → Commits Action → Pushes to server →
Other users receive Action update → Keyframes appear in timeline
```

### 3. Enhanced Detection System

The extension uses a two-stage detection system in [handlers.py](multi_user/handlers.py):

**Stage 1: Object Update Detection**
- Monitors Blender's dependency graph for object changes
- Tracks which objects were updated during a depsgraph cycle
- Collects updated objects in a list for further processing

**Stage 2: Action Synchronization**
- After processing all object updates, checks each updated object for animation data
- If an object has an attached Action, explicitly commits and pushes it
- Ensures keyframes sync even if the Action itself wasn't directly marked as updated

## What Users Will See

### Adding Keyframes

**User A** (adds keyframe):
1. Select object
2. Press `I` to insert keyframe (or use auto-key)
3. Keyframe appears in timeline
4. Action is automatically synced

**User B** (receives keyframe):
1. Sees keyframe appear in timeline within ~0.1 seconds
2. Can immediately select and edit the keyframe
3. Can add additional keyframes to the same Action
4. Can see animation playback

### Editing Keyframes

All users can:
- **Move keyframes** - Drag keyframes in the timeline
- **Change values** - Edit keyframe values in properties or graph editor
- **Delete keyframes** - Remove keyframes from the timeline
- **Change interpolation** - Switch between linear, bezier, constant, etc.
- **Adjust handles** - Modify bezier curve handles in the graph editor

Changes from any user sync to all other users automatically.

### Timeline Display

The timeline will show:
- **All keyframes** from all users (displayed as diamonds on the timeline)
- **Keyframe colors** based on channel type (position, rotation, scale)
- **Multiple keyframes** if users add keyframes on the same frame for different properties

## Technical Details

### Code Changes

**[multi_user/handlers.py:80-128](multi_user/handlers.py)**
```python
# Track updated objects to sync their actions
updated_objects = []

# Process depsgraph updates
for update in reversed(dependency_updates):
    # ... process updates ...

    # Track objects for action sync
    if isinstance(update.id, bpy.types.Object):
        updated_objects.append(update.id)

# Sync actions for updated objects (keyframes)
for obj in updated_objects:
    if obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action
        if hasattr(action, 'uuid'):
            action_node = session.repository.graph.get(action.uuid)
            if action_node and action_node.state == UP:
                porcelain.commit(session.repository, action.uuid)
                porcelain.push(session.repository, 'origin', action.uuid)
```

**[multi_user/bl_types/bl_action.py:267](multi_user/bl_types/bl_action.py)**
```python
class BlAction(ReplicatedDatablock):
    use_delta = True
    bl_id = "actions"
    bl_class = bpy.types.Action
    bl_check_common = True  # ← This allows any user to edit Actions
```

### What Gets Synchronized

For each Action, the following data is synced:

- **F-Curves** (animation curves for each property)
  - Data path (e.g., `location[0]` for X position)
  - Array index (which component: X, Y, Z)
  - Keyframe points:
    - Frame number
    - Value
    - Handle positions (left and right)
    - Handle types (auto, vector, aligned, free)
    - Interpolation mode (bezier, linear, constant)
    - Easing type

- **Action metadata**
  - Action name
  - ID root type (what type of object uses this action)

## Troubleshooting

### Keyframes Not Appearing?

1. **Check connection** - Ensure both users are connected to the same session
2. **Check object ownership** - The object must be selected/owned by the user adding keyframes
3. **Check timeline** - Make sure you're viewing the correct frame range
4. **Check logs** - Look for "Synced action" messages in the Blender console

### Keyframes Appearing But Can't Edit?

1. **Select the object** - You must own the object to edit its keyframes
2. **Check auto-key** - Auto-key mode may interfere with manual keyframe editing
3. **Refresh** - Switch to another frame and back to refresh the timeline

### Performance Issues with Many Keyframes?

1. **Increase update rate** - In preferences, try 0.2s or 0.5s instead of 0.1s
2. **Reduce keyframe density** - Use fewer keyframes or bake animation less frequently
3. **Work in separate scenes** - Use the multi-scene feature to isolate complex animations

## Best Practices

### For Animators

1. **Coordinate who animates what** - While all users can edit keyframes, it's best to divide work by object or by animation property
2. **Use descriptive Action names** - Helps identify which animation is which
3. **Communicate before major changes** - Let others know before deleting or moving large numbers of keyframes
4. **Save regularly** - Use the session backup feature to save animation progress

### For Technical Directors

1. **Monitor performance** - Watch network usage and adjust update rate if needed
2. **Test with your team** - Ensure all users have sufficient internet bandwidth
3. **Use version control** - For final animations, consider exporting to files and using git
4. **Document workflows** - Create team guidelines for keyframe editing

## Example Workflow

### Collaborative Character Animation

**Scenario**: Two animators working on a character walk cycle

**User A (Animator 1)**:
1. Connects to session
2. Selects character armature
3. Adds keyframes for legs (frame 1, 12, 24)
4. Adjusts timing in graph editor

**User B (Animator 2)**:
1. Connects to session
2. Waits for User A to finish leg animation (sees keyframes appear)
3. Selects same character armature
4. Adds keyframes for arms (frame 1, 12, 24)
5. Both animators' keyframes coexist on the timeline

**Result**: Complete walk cycle with both leg and arm animation, created collaboratively in real-time.

### Scene-Based Animation Organization

**Scenario**: Multiple animators working on different shots

1. **Create scenes for each shot**:
   - Shot_01, Shot_02, Shot_03
2. **Each animator works in their scene**:
   - Animator A in Shot_01
   - Animator B in Shot_02
3. **Import shared assets** between scenes:
   - Use "Import Objects" to bring character from Shot_01 to Shot_02
   - Character shares same Action datablock
   - Keyframes from both shots are visible

## Related Features

- **Timeline Sync** - Optionally synchronize playback across users (see preferences)
- **Auto-Update System** - Get notified when new versions with animation improvements are available
- **Multi-Scene Management** - Organize complex projects with multiple scenes
- **Object Import** - Share animated objects between scenes

## Support

If you encounter issues with keyframe synchronization:

1. Check the [troubleshooting guide](README.md#troubleshooting)
2. Look for error messages in the Blender console (Window → Toggle System Console)
3. Report issues on [GitHub](https://github.com/AvvyB/blender-multi-user/issues)

---

**Version**: 0.7.0
**Last Updated**: 2025-01-10
