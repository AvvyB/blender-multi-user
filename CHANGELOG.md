# Changelog

All notable changes to this project will be documented in this file.

## [0.0.2] - 2020-02-28

### Added

- Blender animation features support (alpha).
  - Action.
  - Armature (Unstable).
  - Shape key.
  - Drivers.
  - Constraints.
- Snap to user timeline tool.
- Light probes support (only since 2.83).
- Metaballs support.
- Improved modifiers support.
- Online documentation.
- Improved Undo handling.
- Improved overall session handling:
  - Time To Leave : ensure clients/server disconnect automatically on connection lost.
  - Ping: show clients latency.
  - Non-blocking connection.
  - Connection state tracking.
- Service communication layer to manage background daemons.

### Changed

- UI revamp:
  - Show users frame.
  - Expose IPC(inter process communication) port.
  - New user list.
  - Progress bar to track connection status.
- Right management takes view-layer in account for object selection.
- Use a basic BFS approach for replication graph pre-load.
- Serialization is now based on marshal (2x performance improvements).
- Let pip chose python dependencies install path.

## [0.0.3] - 2020-07-29

### Added

- Auto updater support
- Big Performances improvements on Meshes, Gpencils, Actions
- Multi-scene workflow support
- Render setting synchronization
- Kick command
- Dedicated server with a basic command set
- Administrator session status
- Tests
- Blender 2.83-2.90 support

### Changed

- Config is now stored in blender user preference
- Documentation update
- Connection protocol
- UI revamp:
  - user localization
  - repository init

### Removed

- Unused strict right management strategy
- Legacy config management system

## [0.0.4] - preview

### Added

- Dependency graph driven updates [experimental]
- Optional Edit Mode update
- Late join mechanism 
- Sync Axis lock replication
- Sync collection offset
- Sync camera  orthographic scale
- Logging basic configuration (file output and level)
- Object visibility type replication

### Changed

- Auto updater now handle installation from branches
- use uuid for collection loading

### Fixed

- Prevent unsuported datatypes to crash the session
- Modifier vertex group assignation