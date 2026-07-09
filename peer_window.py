import gi

from peer_discovery import advertise_self, discover_peers
from settings_store import load_settings

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from peer_store import get_pending_peers, get_paired_peers, set_peer_status


class PeerWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="ClipQR Peers")
        self.set_default_size(420, 400)
        self.set_position(Gtk.WindowPosition.CENTER)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        outer.set_border_width(16)
        self.add(outer)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_label = Gtk.Label(label="Peer Devices")
        title_label.set_xalign(0)
        title_label.set_hexpand(True)
        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", lambda _b: self.refresh())
        header.pack_start(title_label, True, True, 0)
        header.pack_end(refresh_btn, False, False, 0)
        outer.pack_start(header, False, False, 0)

        self.pending_label = Gtk.Label(label="Pending")
        self.pending_label.set_xalign(0)
        outer.pack_start(self.pending_label, False, False, 0)

        self.pending_box = Gtk.ListBox()
        self.pending_box.set_selection_mode(Gtk.SelectionMode.NONE)
        outer.pack_start(self.pending_box, False, False, 0)

        outer.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4)

        paired_label = Gtk.Label(label="Paired")
        paired_label.set_xalign(0)
        outer.pack_start(paired_label, False, False, 0)

        self.paired_box = Gtk.ListBox()
        self.paired_box.set_selection_mode(Gtk.SelectionMode.NONE)
        outer.pack_start(self.paired_box, False, False, 0)

        self.refresh()

    def refresh(self):
        for child in self.pending_box.get_children():
            self.pending_box.remove(child)
        for child in self.paired_box.get_children():
            self.paired_box.remove(child)

        pending = get_pending_peers()
        if pending:
            self.pending_label.show()
            for name, info in pending.items():
                self.pending_box.add(self._build_pending_row(name, info))
        else:
            self.pending_label.hide()

        paired = get_paired_peers()
        if not paired:
            empty = Gtk.Label(label="No paired devices yet.")
            self.paired_box.add(empty)
        else:
            for name, info in paired.items():
                self.paired_box.add(self._build_paired_row(name, info))

        self.pending_box.show_all()
        self.paired_box.show_all()

    def _build_pending_row(self, name, info):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(4)
        box.set_margin_bottom(4)

        label = Gtk.Label(label=f"{name.split('.')[0]}  ({info['ip']}:{info['port']})")
        label.set_xalign(0)
        label.set_hexpand(True)

        approve_btn = Gtk.Button(label="Approve")
        approve_btn.connect("clicked", self._make_status_handler(name, "paired"))

        ignore_btn = Gtk.Button(label="Ignore")
        ignore_btn.connect("clicked", self._make_status_handler(name, "ignored"))

        box.pack_start(label, True, True, 0)
        box.pack_end(ignore_btn, False, False, 0)
        box.pack_end(approve_btn, False, False, 0)

        row.add(box)
        return row

    def _build_paired_row(self, name, info):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(4)
        box.set_margin_bottom(4)

        label = Gtk.Label(label=f"{name.split('.')[0]}  ({info['ip']}:{info['port']})")
        label.set_xalign(0)
        label.set_hexpand(True)

        unpair_btn = Gtk.Button(label="Unpair")
        unpair_btn.connect("clicked", self._make_status_handler(name, "ignored"))

        box.pack_start(label, True, True, 0)
        box.pack_end(unpair_btn, False, False, 0)

        row.add(box)
        return row

    def _make_status_handler(self, name, new_status):
        def handler(_button):
            set_peer_status(name, new_status)
            self.refresh()
        return handler


def _standalone_test():
    import time
    from peer_store import upsert_discovered_peer

    my_ip = get_current_lan_ip()
    my_port = load_settings()["port"]

    def on_found(name, ip, port):
        if ip == my_ip and port == my_port:
            print(f"(ignoring self: {name})")
            return
        print(f"Found peer: {name} at {ip}:{port}")
        upsert_discovered_peer(name, ip, port)

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
