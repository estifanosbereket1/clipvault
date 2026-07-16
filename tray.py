import os

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import AyatanaAppIndicator3, Gtk


def setup_tray_icon(on_open, on_settings, on_playback, on_peers,on_send_from_phone, on_quit, on_check_updates, on_about, on_uninstall):
    indicator = AyatanaAppIndicator3.Indicator.new(
        "clipvault",
        "edit-copy",
        AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )
    indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons", "app-icon.png")
    if os.path.exists(icon_path):
        indicator.set_icon_full(icon_path, "ClipVault")

    menu = Gtk.Menu()

    open_item = Gtk.MenuItem(label="Open Clipboard History")
    open_item.connect("activate", lambda _item: on_open())
    menu.append(open_item)

    playback_item = Gtk.MenuItem(label="Clipboard Playback")
    playback_item.connect("activate", lambda _item: on_playback())
    menu.append(playback_item)

    peers_item = Gtk.MenuItem(label="Peer Devices")
    peers_item.connect("activate", lambda _item: on_peers())
    menu.append(peers_item)

    send_item = Gtk.MenuItem(label="Send from Phone")
    send_item.connect("activate", lambda _item: on_send_from_phone())
    menu.append(send_item)

    menu.append(Gtk.SeparatorMenuItem())

    settings_item = Gtk.MenuItem(label="Settings")
    settings_item.connect("activate", lambda _item: on_settings())
    menu.append(settings_item)

    menu.append(Gtk.SeparatorMenuItem())

    update_item = Gtk.MenuItem(label="Check for Updates")
    update_item.connect("activate", lambda _item: on_check_updates())
    menu.append(update_item)

    about_item = Gtk.MenuItem(label="About ClipVault")
    about_item.connect("activate", lambda _item: on_about())
    menu.append(about_item)

    menu.append(Gtk.SeparatorMenuItem())

    uninstall_item = Gtk.MenuItem(label="Uninstall ClipVault")
    uninstall_item.get_style_context().add_class("uninstall-menu-item")
    uninstall_item.connect("activate", lambda _item: on_uninstall())
    menu.append(uninstall_item)

    quit_item = Gtk.MenuItem(label="Quit")
    quit_item.connect("activate", lambda _item: on_quit())
    menu.append(quit_item)

    menu.show_all()
    indicator.set_menu(menu)

    return indicator


def _standalone_test():
    def on_open(): print("Open clicked!")
    def on_settings(): print("Settings clicked!")
    def on_playback(): print("Playback clicked!")
    def on_peers(): print("Peers clicked!")
    def on_check_updates(): print("Check updates clicked!")
    def on_about(): print("About clicked!")
    def on_uninstall(): print("Uninstall clicked!")
    def on_quit():
        print("Quit clicked, exiting.")
        Gtk.main_quit()

    indicator = setup_tray_icon(
        on_open, on_settings, on_playback, on_peers, on_quit,
        on_check_updates, on_about, on_uninstall,
    )
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
