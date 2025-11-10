#!/usr/bin/env python3
"""
Standalone Multi-User Blender Server for Internet Deployment

This script allows you to run a dedicated server on a cloud instance
for internet-based Blender collaboration.

Usage:
    python standalone_server.py --port 5555 --admin-password myAdminPass --server-password myServerPass

Requirements:
    - Python 3.10+
    - pyzmq
    - deepdiff
    - orderly_set
    - replication
"""

import sys
from pathlib import Path

# Add the replication library to the path
replication_wheel = Path(__file__).parent.parent / "multi_user" / "wheels" / "replication-0.9.10-py3-none-any.whl"

if replication_wheel.exists():
    sys.path.insert(0, str(replication_wheel))
else:
    print(f"ERROR: Replication wheel not found at {replication_wheel}")
    print("Please ensure you have the multi-user addon structure intact.")
    sys.exit(1)

# Import and run the server
try:
    from replication.server import cli

    if __name__ == '__main__':
        print("=" * 60)
        print("Multi-User Blender Collaboration Server")
        print("=" * 60)
        print()
        cli()
except ImportError as e:
    print(f"ERROR: Failed to import replication library: {e}")
    print("\nPlease ensure all dependencies are installed:")
    print("  pip install pyzmq deepdiff orderly-set")
    sys.exit(1)
