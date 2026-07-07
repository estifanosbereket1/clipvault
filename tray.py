import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import AyatanaAppIndicator3, Gtk


def setup_tray_icon(on_open, on_settings, on_quit):
    """
    Creates and shows the system tray icon with a right-click menu:
      - Open Clipboard History -> calls on_open()
      - Settings -> calls on_settings()
      - Quit -> calls on_quit()

    Returns the indicator object. Keep a reference to it in main.py --
    if it gets garbage collected, the tray icon can disappear.
    """
    indicator = AyatanaAppIndicator3.Indicator.new(
        "clipqr",
        "edit-copy",
        AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )
    indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)

    menu = Gtk.Menu()

    open_item = Gtk.MenuItem(label="Open Clipboard History")
    open_item.connect("activate", lambda _item: on_open())
    menu.append(open_item)

    settings_item = Gtk.MenuItem(label="Settings")
    settings_item.connect("activate", lambda _item: on_settings())
    menu.append(settings_item)

    separator = Gtk.SeparatorMenuItem()
    menu.append(separator)

    quit_item = Gtk.MenuItem(label="Quit")
    quit_item.connect("activate", lambda _item: on_quit())
    menu.append(quit_item)

    menu.show_all()
    indicator.set_menu(menu)

    return indicator


def _standalone_test():
    def on_open():
        print("Open clicked!")

    def on_settings():
        print("Settings clicked!")

    def on_quit():
        print("Quit clicked, exiting.")
        Gtk.main_quit()

    indicator = setup_tray_icon(on_open, on_settings, on_quit)
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
