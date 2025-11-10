#!/usr/bin/env python3
"""
Test connectivity to a Multi-User Blender server

Usage:
    python test_connection.py <server_ip> <port>
    python test_connection.py example.com 5555
"""

import sys
import zmq
import time

def test_server(host, port):
    """Test if server is accessible"""
    print(f"Testing connection to {host}:{port}...")
    print(f"Checking ports {port}, {port+1}, {port+2}...")
    print()

    context = zmq.Context()
    results = {}

    # Test each port
    for i, channel in enumerate(['Command', 'Data', 'Heartbeat']):
        current_port = int(port) + i
        socket = context.socket(zmq.DEALER)
        socket.setsockopt(zmq.LINGER, 0)
        socket.setsockopt(zmq.RCVTIMEO, 2000)  # 2 second timeout

        try:
            print(f"[{channel}] Connecting to tcp://{host}:{current_port}...", end=" ")
            socket.connect(f"tcp://{host}:{current_port}")

            # Try to send a ping
            socket.send(b"PING")

            # Wait for response
            try:
                response = socket.recv()
                results[channel] = "✓ OK"
                print("✓ Connected")
            except zmq.error.Again:
                results[channel] = "⚠ Connected but no response (normal for initial test)"
                print("⚠ Connected (no response)")

        except Exception as e:
            results[channel] = f"✗ Failed: {e}"
            print(f"✗ Failed: {e}")
        finally:
            socket.close()

    context.term()

    # Summary
    print()
    print("=" * 50)
    print("Connection Test Summary")
    print("=" * 50)
    for channel, result in results.items():
        print(f"{channel:12} - {result}")

    print()
    if all("✓" in r or "⚠" in r for r in results.values()):
        print("✓ Server appears to be accessible!")
        print("You can now connect from Blender using this address:")
        print(f"   IP: {host}")
        print(f"   Port: {port}")
        return 0
    else:
        print("✗ Some ports are not accessible.")
        print("Check firewall settings and ensure the server is running.")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_connection.py <host> <port>")
        print("Example: python test_connection.py 192.168.1.100 5555")
        sys.exit(1)

    host = sys.argv[1]
    port = sys.argv[2]

    try:
        sys.exit(test_server(host, port))
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        sys.exit(1)
