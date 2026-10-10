#!/usr/bin/env python3
"""
p2p-sync: Zero-config encrypted peer-to-peer file synchronization CLI.
Built by Auto Qwen AI.
"""

import os
import sys
import argparse
import asyncio
import uuid
import logging
from p2p_sync.crypto import SyncCrypto
from p2p_sync.manifest import SyncManifest
from p2p_sync.discovery import PeerDiscovery
from p2p_sync.node import P2PNode

CONFIG_DIR = os.path.expanduser("~/.p2p-sync")
KEY_FILE = os.path.join(CONFIG_DIR, "secret.key")

def setup_logging(verbose: bool = False):
    lvl = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=lvl, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

def get_or_create_key() -> str:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    key = SyncCrypto.generate_new_key()
    with open(KEY_FILE, "w", encoding="utf-8") as f:
        f.write(key)
    return key

def cmd_keygen(args):
    key = SyncCrypto.generate_new_key()
    print(f"Generated Cluster Encryption Key:\n{key}\n")
    print("Share this key securely with your other peer machines.")

def cmd_status(args):
    sync_dir = os.path.abspath(args.dir)
    print(f"=== P2P-Sync Status ===")
    print(f"Sync Directory: {sync_dir}")
    if not os.path.exists(sync_dir):
        print("Directory does not exist yet.")
        return

    manifest = SyncManifest(sync_dir).scan()
    print(f"Tracked Files: {len(manifest)}")
    for p, info in sorted(manifest.items()):
        print(f"  - {p} ({info['size']} bytes, hash: {info['hash'][:10]}...)")

async def run_sync_loop(node: P2PNode, discovery: PeerDiscovery, interval: int = 5):
    discovery.start()
    await node.start_server()
    print(f"[*] P2P Node started (ID: {node.node_id}) on TCP port {node.port}")
    print(f"[*] Watching directory: {node.sync_dir}")
    print("[*] Broadcasting and listening for peers on LAN (Ctrl+C to stop)...")

    try:
        while True:
            peers = discovery.get_active_peers()
            if peers:
                for p in peers:
                    await node.sync_with_peer(p['ip'], p['port'])
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        pass
    finally:
        discovery.stop()
        await node.stop()

def cmd_start(args):
    setup_logging(args.verbose)
    sync_dir = os.path.abspath(args.dir)
    os.makedirs(sync_dir, exist_ok=True)

    key = args.key or get_or_create_key()
    node_id = str(uuid.uuid4())[:8]

    node = P2PNode(node_id, sync_dir, key, port=args.port)
    discovery = PeerDiscovery(node_id, tcp_port=args.port, broadcast_port=args.broadcast_port)

    try:
        asyncio.run(run_sync_loop(node, discovery, interval=args.interval))
    except KeyboardInterrupt:
        print("\n[*] P2P Sync stopped cleanly.")

def main():
    parser = argparse.ArgumentParser(
        prog="p2p-sync",
        description="Zero-config encrypted peer-to-peer file synchronization between PCs without 3rd-party servers."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: start
    p_start = subparsers.add_parser("start", help="Start the P2P sync daemon for a directory")
    p_start.add_argument("--dir", default="./sync", help="Directory to synchronize (default: ./sync)")
    p_start.add_argument("--key", default="", help="Cluster encryption key (uses stored key if omitted)")
    p_start.add_argument("--port", type=int, default=8990, help="TCP port for file transfer (default: 8990)")
    p_start.add_argument("--broadcast-port", type=int, default=8765, help="UDP broadcast port (default: 8765)")
    p_start.add_argument("--interval", type=int, default=5, help="Sync poll interval in seconds (default: 5)")
    p_start.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging")

    # Command: status
    p_status = subparsers.add_parser("status", help="Inspect local file manifests and hashes")
    p_status.add_argument("--dir", default="./sync", help="Directory to inspect")

    # Command: keygen
    subparsers.add_parser("keygen", help="Generate a new shared encryption key")

    args = parser.parse_args()
    if args.command == "start":
        cmd_start(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "keygen":
        cmd_keygen(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
