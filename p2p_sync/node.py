import asyncio
import json
import os
import struct
import logging
from .crypto import SyncCrypto
from .manifest import SyncManifest

logger = logging.getLogger("P2PNode")

class P2PNode:
    """Async encrypted peer node for file syncing."""

    def __init__(self, node_id: str, sync_dir: str, crypto_key: str, port: int = 8990):
        self.node_id = node_id
        self.sync_dir = os.path.abspath(sync_dir)
        self.crypto = SyncCrypto(crypto_key.encode("utf-8"))
        self.port = port
        self.manifest_mgr = SyncManifest(self.sync_dir)
        self._server = None

    async def start_server(self):
        self._server = await asyncio.start_server(self.handle_peer, "0.0.0.0", self.port)
        logger.info(f"P2P Node {self.node_id} listening on port {self.port}")

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def send_msg(self, writer: asyncio.StreamWriter, msg_type: str, payload: dict):
        raw = json.dumps({"type": msg_type, "data": payload}).encode("utf-8")
        encrypted = self.crypto.encrypt(raw)
        # 4-byte length prefix + encrypted body
        writer.write(struct.pack("!I", len(encrypted)) + encrypted)
        await writer.drain()

    async def read_msg(self, reader: asyncio.StreamReader) -> dict:
        header = await reader.readexactly(4)
        length = struct.unpack("!I", header)[0]
        encrypted = await reader.readexactly(length)
        decrypted = self.crypto.decrypt(encrypted)
        return json.loads(decrypted.decode("utf-8"))

    async def handle_peer(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            # 1. Receive handshake / manifest
            msg = await self.read_msg(reader)
            if msg.get("type") == "manifest_request":
                local_m = self.manifest_mgr.scan()
                await self.send_msg(writer, "manifest_response", {"manifest": local_m, "node_id": self.node_id})

            elif msg.get("type") == "file_request":
                rel_path = msg["data"]["rel_path"]
                full_path = os.path.join(self.sync_dir, rel_path)
                if os.path.exists(full_path):
                    with open(full_path, "rb") as f:
                        file_bytes = f.read()
                    # Encrypt file content
                    enc_bytes = self.crypto.encrypt(file_bytes)
                    await self.send_msg(writer, "file_data", {
                        "rel_path": rel_path,
                        "data_hex": enc_bytes.hex()
                    })

        except Exception as e:
            logger.debug(f"Peer connection error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def sync_with_peer(self, peer_ip: str, peer_port: int):
        """Connects to a peer, exchanges manifests, and pulls missing/updated files."""
        try:
            reader, writer = await asyncio.open_connection(peer_ip, peer_port)
            # Request manifest
            await self.send_msg(writer, "manifest_request", {"node_id": self.node_id})
            resp = await self.read_msg(reader)

            if resp.get("type") == "manifest_response":
                remote_m = resp["data"]["manifest"]
                local_m = self.manifest_mgr.scan()
                to_pull, _ = SyncManifest.diff(local_m, remote_m)

                writer.close()
                await writer.wait_closed()

                # Fetch needed files
                for rel_path in to_pull:
                    await self.fetch_file_from_peer(peer_ip, peer_port, rel_path)

        except Exception as e:
            logger.debug(f"Sync with {peer_ip}:{peer_port} failed: {e}")

    async def fetch_file_from_peer(self, peer_ip: str, peer_port: int, rel_path: str):
        try:
            reader, writer = await asyncio.open_connection(peer_ip, peer_port)
            await self.send_msg(writer, "file_request", {"rel_path": rel_path})
            resp = await self.read_msg(reader)
            if resp.get("type") == "file_data":
                enc_bytes = bytes.fromhex(resp["data"]["data_hex"])
                file_bytes = self.crypto.decrypt(enc_bytes)
                
                target_path = os.path.join(self.sync_dir, rel_path)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "wb") as f:
                    f.write(file_bytes)
                logger.info(f"Synchronized file: {rel_path}")
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            logger.warning(f"Failed to fetch {rel_path} from {peer_ip}: {e}")
