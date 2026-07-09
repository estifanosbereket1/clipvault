import json
import os
from pathlib import Path

from settings_store import get_settings_path


def get_peers_path() -> Path:
    return get_settings_path().parent / "peers.json"


def load_peers() -> dict:
    """
    Returns a dict keyed by peer service name, each value like:
    {"status": "pending"|"paired"|"ignored", "ip": "...", "port": 8000}
    """
    path = get_peers_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_peers(peers: dict):
    path = get_peers_path()
    with open(path, "w") as f:
        json.dump(peers, f, indent=2)


def upsert_discovered_peer(name: str, ip: str, port: int):
    """
    Called whenever discovery finds a peer. If we've never seen this peer
    before, adds it as 'pending'. If we already know it, just updates its
    current ip/port (in case it changed), preserving its existing status.
    """
    peers = load_peers()
    if name in peers:
        peers[name]["ip"] = ip
        peers[name]["port"] = port
    else:
        peers[name] = {"status": "pending", "ip": ip, "port": port}
    save_peers(peers)


def set_peer_status(name: str, status: str):
    peers = load_peers()
    if name in peers:
        peers[name]["status"] = status
        save_peers(peers)

def get_peer_last_sync(name: str) -> str:
    peers = load_peers()
    if name in peers:
        return peers[name].get("last_sync", "2020-01-01 00:00:00")
    return "2020-01-01 00:00:00"


def set_peer_last_sync(name: str, timestamp: str):
    peers = load_peers()
    if name in peers:
        peers[name]["last_sync"] = timestamp
        save_peers(peers)


def get_pending_peers() -> dict:
    return {name: info for name, info in load_peers().items() if info["status"] == "pending"}


def get_paired_peers() -> dict:
    return {name: info for name, info in load_peers().items() if info["status"] == "paired"}
