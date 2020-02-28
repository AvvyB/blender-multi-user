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