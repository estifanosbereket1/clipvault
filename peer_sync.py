
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import time


import threading
import requests

from storage import add_entry
from peer_store import get_paired_peers, get_peer_last_sync, set_peer_last_sync

SYNC_INTERVAL_SECONDS = 8


def pull_from_peer(peer_name: str, peer_info: dict):
    """
    Asks one paired peer for anything new since our last successful sync
    with them, and inserts whatever comes back, tagged with their origin.
    """
    ip = peer_info["ip"]
    port = peer_info["port"]
    since = get_peer_last_sync(peer_name)

    url = f"https://{ip}:{port}/sync/pull"
    try:
        response = requests.get(url, params={"since": since}, verify=False, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Sync with {peer_name} failed: {e}")
        return

    entries = response.json()
    latest_timestamp = since

    for entry in entries:
        add_entry(entry["content"], origin=peer_name)
        if entry["created_at"] > latest_timestamp:
            latest_timestamp = entry["created_at"]

    if entries:
        set_peer_last_sync(peer_name, latest_timestamp)


def start_sync_loop():
    """
    Runs forever, periodically pulling from every currently-paired peer.
    Intended to run in a background thread.
    """
    while True:
        peers = get_paired_peers()
        for name, info in peers.items():
            pull_from_peer(name, info)
        time.sleep(SYNC_INTERVAL_SECONDS)


def _standalone_test():
    start_sync_loop()


if __name__ == "__main__":
    _standalone_test()
