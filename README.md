# p2p-sync

> **Zero-config encrypted peer-to-peer file synchronization between PCs without 3rd-party servers.**  
> Built and tested autonomously by **Auto Qwen AI**.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/mak74ik/p2p-sync/blob/main/LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## 🌟 Features

- **No Central Servers / Relays:** Direct machine-to-machine transfer over local network and mesh VPNs (Tailscale / ZeroTier).
- **Zero-Config LAN Discovery:** Autonomous peer beacon discovery via UDP broadcast — machines discover each other instantly.
- **End-to-End Encryption:** Authenticated Fernet (AES-128-CBC + HMAC-SHA256) data encryption for all transferred file blocks.
- **Delta Sync with SHA-256:** Only syncs new or modified files based on content hash digests and timestamps.
- **Lightweight Single Process:** Pure asynchronous Python (`asyncio`), minimal dependencies (`cryptography`).

---

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/mak74ik/p2p-sync.git
cd p2p-sync
pip install cryptography
```

### 2. Generate a Shared Cluster Key

On the primary PC, generate a secret encryption key:

```bash
python3 main.py keygen
```

Copy the generated key to your other computers.

### 3. Start Syncing

On PC 1:
```bash
python3 main.py start --dir ~/Documents/SyncVault --key <YOUR_SECRET_KEY>
```

On PC 2:
```bash
python3 main.py start --dir ~/Documents/SyncVault --key <YOUR_SECRET_KEY>
```

Both nodes will automatically discover each other on the local network, exchange manifests, and synchronize files in real-time.

### 4. Check Sync Status

```bash
python3 main.py status --dir ~/Documents/SyncVault
```

---

## 🧪 Running Tests

```bash
python3 -m unittest discover -s tests
```

---

## 👥 Credits
Developed autonomously by **Auto Qwen AI**:
- 🤖 **Autonomous Engine**: Auto Qwen AI Pipeline
- 🛡️ **Security & Code Review**: Verified & Sandboxed
- 📦 **Architecture**: Local-First P2P File Synchronization Protocol
