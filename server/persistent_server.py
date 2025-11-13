#!/usr/bin/env python3
"""
Persistent Multi-User Blender Server with Auto-Save

This server wrapper adds persistent storage to the replication server:
- Saves session data every 2 minutes
- Saves on user disconnect
- Automatically restores latest session on startup

Features:
- Automatic session snapshots to disk
- Recovery from server restarts
- Timestamped backups
- Configurable save intervals
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


class PersistentSessionManager:
    """Manages persistent storage of session data"""

    def __init__(self):
        self.repository = None
        self.last_save_time = 0
        self.save_timer = None
        self.shutdown_flag = False

    def set_repository(self, repository):
        """Set the repository to persist"""
        self.repository = repository

    def save_session(self, reason="periodic"):
        """Save current session state to disk"""
        if not self.repository:
            logging.debug("No repository to save")
            return

        try:
            # Create snapshot data
            snapshot_data = {
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'reason': reason,
                'graph': self.repository.graph,
                'users': getattr(self.repository, 'online_users', {}),
                'metadata': getattr(self.repository, 'metadata', {}),
            }

            # Save to main snapshot file
            with open(SNAPSHOT_FILE, 'wb') as f:
                pickle.dump(snapshot_data, f)

            # Save metadata as JSON for inspection
            metadata = {
                'timestamp': snapshot_data['timestamp'],
                'datetime': snapshot_data['datetime'],
                'reason': reason,
                'user_count': len(snapshot_data['users']),
                'node_count': len(snapshot_data['graph'].nodes) if hasattr(snapshot_data['graph'], 'nodes') else 0,
            }

            with open(METADATA_FILE, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = BACKUP_DIR / f'snapshot_{timestamp}.pkl'

            with open(backup_file, 'wb') as f:
                pickle.dump(snapshot_data, f)

            # Clean old backups
            self._cleanup_old_backups()

            self.last_save_time = time.time()
            logging.info(f"Session saved to disk (reason: {reason})")
            logging.info(f"  Snapshot: {SNAPSHOT_FILE}")
            logging.info(f"  Backup: {backup_file}")

        except Exception as e:
            logging.error(f"Failed to save session: {e}")

    def restore_session(self):
        """Restore session from latest snapshot"""
        if not SNAPSHOT_FILE.exists():
            logging.info("No existing session to restore")
            return None

        try:
            with open(SNAPSHOT_FILE, 'rb') as f:
                snapshot_data = pickle.load(f)

            logging.info("Session restored from disk")
            logging.info(f"  Timestamp: {snapshot_data['datetime']}")
            logging.info(f"  Reason: {snapshot_data['reason']}")
            logging.info(f"  Users: {len(snapshot_data['users'])}")

            return snapshot_data

        except Exception as e:
            logging.error(f"Failed to restore session: {e}")
            return None

    def _cleanup_old_backups(self):
        """Remove old backup files, keeping only the latest MAX_BACKUPS"""
        try:
            backups = sorted(BACKUP_DIR.glob('snapshot_*.pkl'))

            if len(backups) > MAX_BACKUPS:
                for old_backup in backups[:-MAX_BACKUPS]:
                    old_backup.unlink()
                    logging.debug(f"Removed old backup: {old_backup.name}")

        except Exception as e:
            logging.error(f"Failed to cleanup old backups: {e}")

    def start_auto_save(self):
        """Start periodic auto-save timer"""
        if self.save_timer:
            self.save_timer.cancel()

        self.save_timer = threading.Timer(SAVE_INTERVAL, self._auto_save_callback)
        self.save_timer.daemon = True
        self.save_timer.start()

        logging.info(f"Auto-save enabled (interval: {SAVE_INTERVAL}s)")

    def _auto_save_callback(self):
        """Callback for periodic saves"""
        if not self.shutdown_flag:
            self.save_session(reason="auto-save")
            self.start_auto_save()  # Schedule next save

    def stop_auto_save(self):
        """Stop auto-save timer"""
        self.shutdown_flag = True
        if self.save_timer:
            self.save_timer.cancel()
            self.save_timer = None

    def shutdown(self):
        """Save session and cleanup before shutdown"""
        logging.info("Shutting down - saving final snapshot...")
        self.stop_auto_save()
        self.save_session(reason="shutdown")


# Global session manager
session_manager = PersistentSessionManager()


def setup_signal_handlers():
    """Setup handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}")
        session_manager.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def wrap_replication_server():
    """Wrap the replication server with persistence layer"""
    from replication import server as replication_server

    # Monkey-patch the server to add persistence hooks
    original_server_class = None

    # Try to find the server class
    for attr_name in dir(replication_server):
        attr = getattr(replication_server, attr_name)
        if isinstance(attr, type) and 'Server' in attr_name:
            original_server_class = attr
            break

    if not original_server_class:
        logging.warning("Could not find server class to wrap - persistence may be limited")
        return

    # Store original methods
    original_init = original_server_class.__init__
    original_on_user_disconnect = getattr(original_server_class, 'on_user_disconnect', None)

    def new_init(self, *args, **kwargs):
        """Wrapped init to restore session and start auto-save"""
        original_init(self, *args, **kwargs)

        # Set repository in session manager
        if hasattr(self, 'repository'):
            session_manager.set_repository(self.repository)

            # Try to restore previous session
            snapshot = session_manager.restore_session()
            if snapshot:
                try:
                    # Restore graph
                    if hasattr(self.repository, 'graph') and snapshot.get('graph'):
                        self.repository.graph = snapshot['graph']
                        logging.info("Repository graph restored")

                    # Restore metadata if present
                    if hasattr(self.repository, 'metadata') and snapshot.get('metadata'):
                        self.repository.metadata = snapshot['metadata']
                        logging.info("Repository metadata restored")

                except Exception as e:
                    logging.error(f"Error restoring session data: {e}")

        # Start auto-save
        session_manager.start_auto_save()

    def new_on_user_disconnect(self, user_id, *args, **kwargs):
        """Wrapped disconnect handler to save on user logout"""
        # Call original handler if it exists
        if original_on_user_disconnect:
            result = original_on_user_disconnect(self, user_id, *args, **kwargs)
        else:
            result = None

        # Save session when user disconnects
        logging.info(f"User disconnected: {user_id}")
        session_manager.save_session(reason=f"user_disconnect:{user_id}")

        return result

    # Apply monkey patches
    original_server_class.__init__ = new_init
    if original_on_user_disconnect:
        original_server_class.on_user_disconnect = new_on_user_disconnect


def main():
    """Main entry point"""
    print("=" * 60)
    print("Multi-User Blender Server with Persistent Storage")
    print("=" * 60)
    print()
    print(f"Data Directory: {DATA_DIR}")
    print(f"Auto-save Interval: {SAVE_INTERVAL} seconds")
    print(f"Max Backups: {MAX_BACKUPS}")
    print()

    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()

    # Check if previous session exists
    if SNAPSHOT_FILE.exists():
        try:
            with open(METADATA_FILE, 'r') as f:
                metadata = json.load(f)
            print("Previous session found:")
            print(f"  Timestamp: {metadata.get('datetime', 'Unknown')}")
            print(f"  Users: {metadata.get('user_count', 0)}")
            print(f"  Nodes: {metadata.get('node_count', 0)}")
            print(f"  Reason: {metadata.get('reason', 'Unknown')}")
            print("\nSession will be automatically restored on first connection")
            print()
        except:
            pass

    # Wrap the replication server
    try:
        wrap_replication_server()
        logging.info("Persistence layer initialized")
    except Exception as e:
        logging.error(f"Failed to initialize persistence layer: {e}")
        logging.warning("Server will run without persistence")

    # Import and run the standard replication server
    try:
        from replication.server import cli
        cli()
    except KeyboardInterrupt:
        logging.info("Server interrupted")
        session_manager.shutdown()
    except Exception as e:
        logging.error(f"Server error: {e}")
        session_manager.shutdown()
        raise


if __name__ == '__main__':
    main()
