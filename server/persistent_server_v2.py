#!/usr/bin/env python3
"""
Persistent Multi-User Blender Server with Auto-Save v2

This version uses a more robust approach:
- Runs auto-save timer independently
- Directly accesses the replication server's repository
- Saves even when no clients are connected
- More reliable data persistence

Features:
- Saves session data every 2 minutes
- Saves on user disconnect
- Automatically restores latest session on startup
"""

import sys
import os
import pickle
import json
import time
import signal
import threading
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    format="%(asctime)s SERVER %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

# Data directory for persistent storage
DATA_DIR = Path(os.getenv('DATA_DIR', '/app/data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_FILE = DATA_DIR / 'session_snapshot.pkl'
METADATA_FILE = DATA_DIR / 'session_metadata.json'
BACKUP_DIR = DATA_DIR / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)

# Save interval in seconds (2 minutes)
SAVE_INTERVAL = int(os.getenv('SAVE_INTERVAL', 120))

# Keep last N backups
MAX_BACKUPS = int(os.getenv('MAX_BACKUPS', 10))

# Global reference to server instance
_server_instance = None
_shutdown_flag = False


def save_session(reason="periodic"):
    """Save current session state to disk"""
    global _server_instance

    if not _server_instance:
        logging.debug("No server instance to save")
        return

    try:
        # Import STATE_ACTIVE constant
        try:
            from replication.constants import STATE_ACTIVE
        except ImportError:
            STATE_ACTIVE = 'ACTIVE'

        # Access repository from server
        repository = None
        if hasattr(_server_instance, 'repository'):
            repository = _server_instance.repository
        elif hasattr(_server_instance, '_repository'):
            repository = _server_instance._repository

        if not repository:
            logging.debug("No repository found on server instance")
            return

        # Check if repository is initialized
        is_initialized = hasattr(repository, 'state') and repository.state == STATE_ACTIVE

        # Create snapshot data
        snapshot_data = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'reason': reason,
            'initialized': is_initialized,
            'graph': repository.graph if hasattr(repository, 'graph') else {},
            'metadata': getattr(repository, 'metadata', {}),
        }

        # Save to main snapshot file
        with open(SNAPSHOT_FILE, 'wb') as f:
            pickle.dump(snapshot_data, f)

        # Save metadata as JSON for inspection
        metadata = {
            'timestamp': snapshot_data['timestamp'],
            'datetime': snapshot_data['datetime'],
            'reason': reason,
            'initialized': is_initialized,
            'node_count': len(snapshot_data['graph'].nodes) if hasattr(snapshot_data.get('graph'), 'nodes') else 0,
        }

        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f'snapshot_{timestamp}.pkl'

        with open(backup_file, 'wb') as f:
            pickle.dump(snapshot_data, f)

        # Clean old backups
        cleanup_old_backups()

        logging.info(f"✓ Session saved to disk (reason: {reason})")
        logging.debug(f"  Snapshot: {SNAPSHOT_FILE}")
        logging.debug(f"  Backup: {backup_file}")

    except Exception as e:
        logging.error(f"Failed to save session: {e}")
        import traceback
        logging.debug(traceback.format_exc())


def restore_session():
    """Restore session from latest snapshot"""
    if not SNAPSHOT_FILE.exists():
        logging.info("No existing session to restore")
        return None

    try:
        with open(SNAPSHOT_FILE, 'rb') as f:
            snapshot_data = pickle.load(f)

        was_initialized = snapshot_data.get('initialized', False)

        logging.info("✓ Session data loaded from disk")
        logging.info(f"  Timestamp: {snapshot_data['datetime']}")
        logging.info(f"  Reason: {snapshot_data['reason']}")
        logging.info(f"  Initialized: {was_initialized}")

        return snapshot_data

    except Exception as e:
        logging.error(f"Failed to restore session: {e}")
        return None


def cleanup_old_backups():
    """Remove old backup files, keeping only the latest MAX_BACKUPS"""
    try:
        backups = sorted(BACKUP_DIR.glob('snapshot_*.pkl'))

        if len(backups) > MAX_BACKUPS:
            for old_backup in backups[:-MAX_BACKUPS]:
                old_backup.unlink()
                logging.debug(f"Removed old backup: {old_backup.name}")

    except Exception as e:
        logging.error(f"Failed to cleanup old backups: {e}")


def auto_save_loop():
    """Background thread that saves periodically"""
    global _shutdown_flag

    logging.info(f"✓ Auto-save enabled (interval: {SAVE_INTERVAL}s)")

    while not _shutdown_flag:
        time.sleep(SAVE_INTERVAL)
        if not _shutdown_flag:
            save_session(reason="auto-save")


def setup_signal_handlers():
    """Setup handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        global _shutdown_flag
        logging.info(f"Received signal {signum}")
        _shutdown_flag = True
        save_session(reason="shutdown")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def apply_persistence_hooks():
    """Apply hooks to replication server for persistence"""
    try:
        from replication.constants import STATE_ACTIVE
    except ImportError:
        STATE_ACTIVE = 'ACTIVE'

    # Get the replication server module
    from replication import server as replication_server

    # Find the server class
    server_class = None
    for attr_name in dir(replication_server):
        attr = getattr(replication_server, attr_name)
        if isinstance(attr, type) and 'Server' in attr_name:
            server_class = attr
            break

    if not server_class:
        logging.warning("Could not find server class to hook")
        return False

    # Store original methods
    original_init = server_class.__init__
    original_on_user_disconnect = getattr(server_class, 'on_user_disconnect', None)

    def new_init(self, *args, **kwargs):
        """Wrapped init to capture server instance and restore session"""
        global _server_instance

        # Call original init
        original_init(self, *args, **kwargs)

        # Store server instance globally
        _server_instance = self
        logging.debug("Server instance captured for persistence")

        # Try to restore previous session
        snapshot = restore_session()
        if snapshot and hasattr(self, 'repository'):
            try:
                # Restore graph
                if 'graph' in snapshot and snapshot['graph']:
                    self.repository.graph = snapshot['graph']
                    logging.info("✓ Repository graph restored")

                # Restore metadata
                if 'metadata' in snapshot and snapshot['metadata']:
                    self.repository.metadata = snapshot['metadata']
                    logging.info("✓ Repository metadata restored")

                # Auto-initialize if was previously initialized
                was_initialized = snapshot.get('initialized', False)
                if was_initialized and hasattr(self.repository, 'state'):
                    self.repository.state = STATE_ACTIVE
                    logging.info(f"✓ Repository automatically initialized to ACTIVE state")
                    logging.info("  Users can connect immediately without re-initialization")

            except Exception as e:
                logging.error(f"Error restoring session data: {e}")
                import traceback
                logging.debug(traceback.format_exc())

    def new_on_user_disconnect(self, user_id, *args, **kwargs):
        """Wrapped disconnect handler to save on user logout"""
        # Call original handler
        result = None
        if original_on_user_disconnect:
            result = original_on_user_disconnect(self, user_id, *args, **kwargs)

        # Save session when user disconnects
        logging.info(f"User disconnected: {user_id}")
        save_session(reason=f"user_disconnect:{user_id}")

        return result

    # Apply hooks
    server_class.__init__ = new_init
    if original_on_user_disconnect:
        server_class.on_user_disconnect = new_on_user_disconnect

    logging.info("✓ Persistence hooks applied")
    return True


def main():
    """Main entry point"""
    print("=" * 70)
    print("Multi-User Blender Server with Persistent Storage v2")
    print("=" * 70)
    print()
    print(f"📁 Data Directory: {DATA_DIR}")
    print(f"⏱️  Auto-save Interval: {SAVE_INTERVAL} seconds")
    print(f"💾 Max Backups: {MAX_BACKUPS}")
    print()

    # Setup signal handlers
    setup_signal_handlers()

    # Check if previous session exists
    if SNAPSHOT_FILE.exists():
        try:
            with open(METADATA_FILE, 'r') as f:
                metadata = json.load(f)
            print("📂 Previous session found:")
            print(f"   Timestamp: {metadata.get('datetime', 'Unknown')}")
            print(f"   Initialized: {metadata.get('initialized', False)}")
            print(f"   Nodes: {metadata.get('node_count', 0)}")
            print(f"   Reason: {metadata.get('reason', 'Unknown')}")
            print()
            print("   → Session will be automatically restored on startup")
            print()
        except:
            pass
    else:
        print("📂 No previous session found (first run)")
        print()

    # Apply persistence hooks
    try:
        success = apply_persistence_hooks()
        if not success:
            logging.warning("Server will run without persistence")
    except Exception as e:
        logging.error(f"Failed to apply persistence hooks: {e}")
        logging.warning("Server will run without persistence")

    # Start auto-save thread
    auto_save_thread = threading.Thread(target=auto_save_loop, daemon=True)
    auto_save_thread.start()

    # Import and run the replication server CLI
    print("🚀 Starting replication server...")
    print()

    try:
        from replication.server import cli
        cli()
    except KeyboardInterrupt:
        logging.info("Server interrupted by user")
        save_session(reason="keyboard_interrupt")
    except Exception as e:
        logging.error(f"Server error: {e}")
        save_session(reason="error")
        raise


if __name__ == '__main__':
    main()
