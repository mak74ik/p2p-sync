import socket
import json
import threading
import time
import logging

logger = logging.getLogger("P2PDiscovery")

class PeerDiscovery:
    """Discovers peer machines on local area network using UDP broadcast."""

    def __init__(self, node_id: str, tcp_port: int, broadcast_port: int = 8765):
        self.node_id = node_id
        self.tcp_port = tcp_port
        self.broadcast_port = broadcast_port
        self.peers = {}  # {node_id: {'ip': ..., 'port': ..., 'last_seen': ...}}
        self._running = False
        self._lock = threading.Lock()

    def start(self):
        self._running = True
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self._listen_thread.start()
        self._broadcast_thread.start()

    def stop(self):
        self._running = False

    def get_active_peers(self, timeout_sec: float = 15.0) -> list:
        now = time.time()
        with self._lock:
            return [p for p in self.peers.values() if (now - p['last_seen']) < timeout_sec]

    def _broadcast_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1.0)

        payload = json.dumps({
            "proto": "p2p-sync-beacon",
            "node_id": self.node_id,
            "port": self.tcp_port
        }).encode("utf-8")

        while self._running:
            try:
                sock.sendto(payload, ("<broadcast>", self.broadcast_port))
            except Exception as e:
                logger.debug(f"Broadcast error: {e}")
            time.sleep(3.0)
        sock.close()

    def _listen_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", self.broadcast_port))
        except Exception as e:
            logger.warning(f"Could not bind broadcast listener port {self.broadcast_port}: {e}")
            return

        sock.settimeout(2.0)
        while self._running:
            try:
                data, addr = sock.recvfrom(2048)
                msg = json.loads(data.decode("utf-8"))
                if msg.get("proto") == "p2p-sync-beacon" and msg.get("node_id") != self.node_id:
                    node_id = msg["node_id"]
                    peer_ip = addr[0]
                    peer_port = msg["port"]
                    with self._lock:
                        self.peers[node_id] = {
                            "node_id": node_id,
                            "ip": peer_ip,
                            "port": peer_port,
                            "last_seen": time.time()
                        }
            except (socket.timeout, json.JSONDecodeError):
                continue
            except Exception as e:
                logger.debug(f"Discovery listener error: {e}")
        sock.close()
