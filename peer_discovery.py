import socket
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceListener
from settings_store import get_current_lan_ip, load_settings

SERVICE_TYPE = "_clipqr._tcp.local."


def advertise_self(port: int, hostname_label: str) -> tuple[Zeroconf, ServiceInfo]:
    """
    Announces this instance on the LAN via mDNS, so other ClipQR instances
    can discover it. Returns (zeroconf_instance, service_info) -- keep both
    alive for as long as you want to stay discoverable; call zeroconf.close()
    and zeroconf.unregister_service(service_info) to stop advertising.
    """
    zeroconf = Zeroconf()

    local_ip = get_current_lan_ip()
    address_bytes = socket.inet_aton(local_ip)

    service_name = f"{hostname_label}.{SERVICE_TYPE}"

    info = ServiceInfo(
        SERVICE_TYPE,
        service_name,
        addresses=[address_bytes],
        port=port,
        properties={},
    )

    zeroconf.register_service(info)
    return zeroconf, info


class _DiscoveryListener(ServiceListener):
    def __init__(self, on_peer_found, on_peer_lost):
        self.on_peer_found = on_peer_found
        self.on_peer_lost = on_peer_lost

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info is None:
            return
        ip = socket.inet_ntoa(info.addresses[0])
        port = info.port
        self.on_peer_found(name, ip, port)

    def remove_service(self, zeroconf, service_type, name):
        self.on_peer_lost(name)

    def update_service(self, zeroconf, service_type, name):
        pass  # not needed for our use case


def discover_peers(on_peer_found, on_peer_lost) -> tuple[Zeroconf, ServiceBrowser]:
    """
    Starts listening for other ClipQR instances on the LAN.
    on_peer_found(name, ip, port) is called when a peer appears.
    on_peer_lost(name) is called when a peer disappears.
    Returns (zeroconf_instance, browser) -- keep both alive to keep listening.
    """
    zeroconf = Zeroconf()
    listener = _DiscoveryListener(on_peer_found, on_peer_lost)
    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener)
    return zeroconf, browser


def _standalone_test():
    import time

    my_ip = get_current_lan_ip()
    my_port = load_settings()["port"]

    def on_found(name, ip, port):
        if ip == my_ip and port == my_port:
            print(f"(ignoring self: {name})")
            return
        print(f"Found peer: {name} at {ip}:{port}")

    def on_lost(name):
        print(f"Lost peer: {name}")

    settings = load_settings()
    zc_advertise, info = advertise_self(settings["port"], hostname_label=socket.gethostname())
    print(f"Advertising self on port {settings['port']}...")

    zc_discover, browser = discover_peers(on_found, on_lost)
    print("Listening for peers... (Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        zc_advertise.unregister_service(info)
        zc_advertise.close()
        zc_discover.close()


if __name__ == "__main__":
    _standalone_test()
