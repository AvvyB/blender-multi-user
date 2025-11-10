# New Features in v0.8.0

Multi-User v0.8.0 is a major update that adds powerful collaboration tools to help teams work together more effectively.

## 🎯 What's New

### 1. Change Tracking System (Git Blame-like)
**See who made which changes to objects**

Track the complete history of changes made to any object in your scene. Perfect for understanding how the scene evolved and who contributed what.

#### Features:
- **Object history** - View all changes made to any object
- **User attribution** - See exactly who made each change
- **Property tracking** - Track changes to location, rotation, scale, materials, and more
- **Timestamps** - Know when each change was made
- **Recent changes view** - See team-wide activity

#### How to Use:
1. **View object history**: Select an object → Multi-User panel → History → "History: [ObjectName]"
2. **View recent changes**: Multi-User panel → History → "View Recent Changes"
3. **See details**: Each change shows date/time, username, property changed, and before/after values

**Example:**
```
[2025-01-10 14:23:15] John    location: (0,0,0) → (1,2,3)
[2025-01-10 14:22:03] Sarah   material: None → Metal.001
[2025-01-10 14:20:45] John    scale: (1,1,1) → (2,2,2)
```

---

### 2. Collaborative Undo/Redo System
**Team-wide undo operations**

Unlike Blender's local undo, this system provides collaborative undo/redo that works across all connected users.

#### Features:
- **Shared undo stack** - All users see the same undo history
- **50 action buffer** - Keep track of the last 50 collaborative actions
- **Smart conflict resolution** - Prevents undo conflicts between users
- **Visual feedback** - Shows number of available undo actions

#### How to Use:
1. Open Multi-User panel → History section
2. Click **"Undo"** to undo the last collaborative action
3. Click **"Redo"** to redo the last undone action
4. See action count: "X actions available"

#### Best Practices:
- **Communicate before big undos** - Let team know if you're undoing multiple actions
- **Use for mistakes** - Quickly recover from accidental changes
- **Complements local undo** - Use Blender's Ctrl+Z for local changes, collaborative undo for synced changes

---

### 3. Task Management System
**Create, assign, and track tasks**

Built-in task management lets teams organize work without external tools.

#### Features:
- **Create tasks** - Add tasks with title and description
- **Assign to users** - Assign tasks to specific team members
- **Link to objects** - Attach tasks to specific objects
- **Status tracking** - To Do, In Progress, Done
- **Filtering** - View tasks by status or assignment
- **Real-time sync** - All users see tasks instantly

#### How to Use:

**Create a Task:**
1. Multi-User panel → Tasks → "New Task"
2. Enter title (required) and description
3. Optionally assign to a user (enter their username)
4. Optionally link to active object
5. Click OK

**View Tasks:**
1. Multi-User panel → Tasks → "All Tasks"
2. Or filter by status: "To Do", "In Progress", "Done"
3. See task counts: "To Do (5)", "In Progress (2)", "Done (12)"

**Update Task Status:**
1. Click "All Tasks" to open task list
2. Find your task
3. Click status button: "To Do", "In Progress", or "Done"

**Delete Task:**
1. Open task list
2. Click "Delete" button on any task

#### Use Cases:
- **Animation tasks**: "Animate character walk cycle" → Assign to animator
- **Modeling tasks**: "Add details to building facade" → Link to building object
- **Review tasks**: "Fix lighting in Scene_02" → Mark as In Progress when working
- **Bug fixes**: "Character hand clipping through wall" → Track until fixed

---

### 4. Team Chat System
**Real-time communication**

Built-in chat eliminates the need for external communication tools.

#### Features:
- **Text messages** - Send messages to all connected users
- **Link sharing** - Paste URLs, clickable in chat
- **Code snippets** - Share Python scripts with syntax preservation
- **Chat history** - All messages saved with session
- **Unread count** - See how many new messages you have
- **Timestamps** - Every message shows time sent

#### How to Use:

**Open Chat:**
- Multi-User panel → Chat → "Open Chat"
- Shows recent 20 messages
- Displays unread message count

**Send Message:**
- Type in "Quick Message" field
- Click "Send"
- Or open full chat window for more space

**Share Links:**
- Just paste the URL: `https://docs.blender.org/manual/en/latest/`
- Appears as clickable link in chat
- Click to open in browser

**Share Code:**
- Wrap code in triple backticks:
```python
import bpy
bpy.ops.mesh.primitive_cube_add()
```
- Shows in code box with "Copy Code" button
- Click to copy to clipboard

#### Chat Tips:
- **Reference objects**: "Check the lighting on MainCharacter"
- **Share resources**: "https://blendermarket.com/products/..."
- **Quick scripts**: Share utility functions
- **Status updates**: "Taking a break, BRB"
- **Coordinate**: "I'm working on Scene_02, don't switch"

#### Message Types:
- **📝 Text** - Regular messages
- **🔗 Link** - URLs (http:// or https://)
- **💻 Code** - Wrapped in ``` (triple backticks)

---

## 📋 Complete Feature List (v0.8.0)

### New in 0.8.0:
1. ✅ Change tracking system (git blame-like)
2. ✅ Collaborative undo/redo
3. ✅ Task management with assignments
4. ✅ Team chat with links and code snippets
5. ✅ Chat history persistence

### From Previous Versions:
6. ✅ Multiple scene support
7. ✅ Object import between scenes
8. ✅ Keyframe synchronization
9. ✅ Timeline sync (optional)
10. ✅ Auto-update notifications
11. ✅ Internet server deployment
12. ✅ 10x faster sync (0.1s)

---

## 🎨 Multi-User Panel Layout

After connecting to a session, the **Multi-User** sidebar panel (press `N`) now has these tabs:

```
┌─────────────────────────────────┐
│        Multi-User Panel         │
├─────────────────────────────────┤
│ 1. Scenes                       │
│    - Create blank/duplicate     │
│    - Switch scenes              │
│    - Import objects             │
├─────────────────────────────────┤
│ 2. Tasks                        │
│    - New Task                   │
│    - View All (15)              │
│    - To Do (5) | Progress (3)  │
├─────────────────────────────────┤
│ 3. History                      │
│    - Undo / Redo               │
│    - View Recent Changes        │
│    - Object History             │
├─────────────────────────────────┤
│ 4. Chat                         │
│    - 3 New Messages             │
│    - Open Chat                  │
│    - Quick Message              │
└─────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### For First-Time Users:

1. **Connect to Server**
   - Edit → Preferences → Multi-User
   - Select server, click "Connect"

2. **Create a Task**
   - Multi-User panel → Tasks → "New Task"
   - "Set up lighting" → Assign to yourself

3. **Send a Chat Message**
   - Multi-User panel → Chat → Type message → Send
   - Say hello to your team!

4. **Make Changes**
   - Move/edit objects as normal
   - Changes sync automatically

5. **View History**
   - Select object → History → "History: ObjectName"
   - See who changed what

6. **Update Task**
   - Tasks → "All Tasks" → Change status to "In Progress"

---

## 💡 Workflow Examples

### Example 1: Animation Team

**Setup:**
- Team Leader creates tasks:
  - "Animate character walk" → Assign to Animator A
  - "Animate character jump" → Assign to Animator B
  - "Review all animations" → Assign to Director

**Work:**
- Animators update task status as they work
- Use chat to coordinate: "Working on frame 50-100"
- Director views change history to see progress

**Review:**
- Director: "The walk looks great!" (in chat)
- "Jump needs more weight" (create new task)
- Animator B marks original task "Done"

### Example 2: Modeling & Texturing

**Setup:**
- Create Scene: "Asset_Library"
- Create Scene: "Main_Scene"
- Modeler works in Asset_Library
- Texture Artist works in Main_Scene

**Work:**
- Modeler: Creates character model
- Texture Artist: Imports character from Asset_Library
- Uses chat: "Model ready for texturing!"
- Texture Artist: Applies materials
- Changes sync back to Asset_Library (linked object)

**Tracking:**
- Use change history to see who modified materials
- Create task: "Add bump maps" → Assign to Texture Artist

---

## 🎯 Best Practices

### Change Tracking:
- **Review regularly** - Check "Recent Changes" to stay updated
- **Investigate issues** - Use object history to debug problems
- **Learn workflows** - See how experienced team members work

### Task Management:
- **Be specific** - "Add details to roof" not "Fix building"
- **Update status** - Keep tasks current so team knows what's happening
- **Link objects** - Makes it easy to find what needs work
- **Clean up** - Delete completed tasks periodically

### Chat:
- **Stay professional** - Chat is saved with session
- **Use code tags** - Wrap scripts in ``` for easy copying
- **Share resources** - Links to tutorials, assets, references
- **Coordinate breaks** - Let team know when you're AFK

### Undo/Redo:
- **Undo early** - Catch mistakes immediately
- **Communicate** - Tell team before big undos
- **Use sparingly** - Not a replacement for proper workflow
- **Local first** - Try Ctrl+Z before collaborative undo

---

## ⚙️ Advanced Tips

### Task Management:
- **Use as bug tracker** - Create task for each bug
- **Sprint planning** - Create all tasks at start of week
- **Progress tracking** - Check "Done" count to see completion rate

### Chat System:
- **Search workaround** - Open chat, screenshot for records
- **Code library** - Save useful scripts from chat
- **Link collection** - Keep resource links in a text file

### Change History:
- **Audit trail** - Know who changed critical objects
- **Learning tool** - See how experts solve problems
- **Conflict resolution** - Determine who made conflicting changes

---

## 🐛 Troubleshooting

### Tasks not showing up?
- Click "Refresh" (file refresh icon) in Tasks panel
- Tasks sync via metadata, may take 1-2 seconds

### Chat messages missing?
- Click "Refresh Messages" button
- Chat syncs last 10 messages per user
- Very old messages may be pruned (500 message limit)

### Change history empty?
- History only tracks changes during current session
- Previous sessions not recorded
- Make a change to start recording

### Undo not working?
- Check if "X actions available" shows 0
- Undo only works for collaborative changes
- Use Ctrl+Z for local Blender undo

---

## 📊 Performance Notes

### Impact on Sync Speed:
- **Chat**: Minimal (10 messages = ~2KB)
- **Tasks**: Minimal (task data < 1KB each)
- **Change tracking**: None (local only, not synced)
- **Undo/Redo**: Minimal (action metadata only)

### Memory Usage:
- **Change history**: ~1MB for 1000 changes
- **Task manager**: ~50KB for 100 tasks
- **Chat**: ~100KB for 500 messages
- **Total overhead**: < 2MB for typical session

---

## 🔮 Coming Soon

Features not yet implemented but planned:

- **Offline mode** - Work offline, auto-sync when reconnecting
- **Local work mode** - Work privately, push changes when ready
- **Geometry nodes sync** - Real-time geometry node network sync
- **Voice chat** - Built-in voice communication
- **User cursors** - See where teammates are looking
- **Annotations** - 3D sticky notes on objects

---

## 📚 Additional Resources

- **[Scene Management Guide](SCENE_MANAGEMENT_GUIDE.md)** - Complete scene workflow guide
- **[Keyframe Sync Guide](KEYFRAME_SYNC.md)** - Animation synchronization details
- **[Server Setup](server/README.md)** - Deploy your own server
- **[Main README](README.md)** - General documentation

---

## ❓ FAQ

**Q: Are tasks private or visible to all users?**
A: All tasks are visible to all connected users. This promotes transparency.

**Q: Can I delete someone else's task?**
A: Yes, any user can delete any task. Trust your team!

**Q: Is chat encrypted?**
A: Chat is sent over the same channel as scene data (ZeroMQ over TCP). Use HTTPS/SSL at the server level for encryption.

**Q: How long is chat history kept?**
A: Last 500 messages kept in memory. Saved with session backups.

**Q: Can I undo someone else's changes?**
A: Yes, collaborative undo works on all users' changes. Coordinate with your team.

**Q: Does change tracking slow down Blender?**
A: No, tracking is lightweight and runs in background.

---

**Version**: 0.8.0
**Release Date**: January 10, 2025
**Requires**: Blender 4.3.0 or later

**Enjoy collaborating! 🎉**
