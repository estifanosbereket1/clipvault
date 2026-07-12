import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk, Gdk, Gio

from palettes import PALETTES
from theme_manager import get_system_theme_is_dark


def _make_color_swatch(hex_color: str, size: int = 20) -> Gtk.DrawingArea:
    area = Gtk.DrawingArea()
    area.set_size_request(size, size)

    def on_draw(widget, cr):
        rgba = Gdk.RGBA()
        rgba.parse(hex_color)
        cr.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
        radius = size / 2
        cr.arc(radius, radius, radius - 1, 0, 2 * 3.14159)
        cr.fill()
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(1)
        cr.arc(radius, radius, radius - 1, 0, 2 * 3.14159)
        cr.stroke()

    area.connect("draw", on_draw)
    return area


def build_system_mode_indicator(system_is_dark: bool) -> Gtk.Box:
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    row.pack_start(Gtk.Label(label="Your system is currently in:"), False, False, 0)

    swatch = _make_color_swatch("#1a1a1a" if system_is_dark else "#f5f5f5")
    row.pack_start(swatch, False, False, 0)

    mode_label = Gtk.Label(label="Dark mode" if system_is_dark else "Light mode")
    row.pack_start(mode_label, False, False, 0)

    return row


class PalettePicker(Gtk.Box):
    def __init__(self, current_palette: str, on_selected):
        """
        current_palette: the palette key currently saved for the system's
        CURRENT mode at construction time.
        on_selected: called with (palette_key) whenever the user picks a new one.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.on_selected = on_selected
        self.radio_group = None

        # Watch for the system flipping dark/light WHILE this window is open,
        # so we're not stuck showing stale info from when the window opened.
        self._gsettings = Gio.Settings.new("org.gnome.desktop.interface")
        self._gsettings.connect("changed::color-scheme", self._on_system_theme_changed)

        system_is_dark = get_system_theme_is_dark()
        self.settings_key = "dark_palette" if system_is_dark else "light_palette"
        self.selected_palette = current_palette

        self._build_contents()

    def _on_system_theme_changed(self, *_args):
        from settings_store import load_settings

        system_is_dark = get_system_theme_is_dark()
        self.settings_key = "dark_palette" if system_is_dark else "light_palette"

        settings = load_settings()
        default = "midnight" if system_is_dark else "daylight"
        self.selected_palette = settings.get(self.settings_key, default)

        self._build_contents()

    def _build_contents(self):
        for child in self.get_children():
            self.remove(child)

        system_is_dark = get_system_theme_is_dark()

        self.pack_start(build_system_mode_indicator(system_is_dark), False, False, 0)
        self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 6)

        self.radio_group = None

        for key, info in PALETTES.items():
            matches_system = info["dark"] == system_is_dark

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            radio = Gtk.RadioButton.new_from_widget(self.radio_group)
            if self.radio_group is None:
                self.radio_group = radio
            radio.set_active(key == self.selected_palette)
            radio.set_sensitive(matches_system)
            radio.connect("toggled", self._make_toggle_handler(key))
            row.pack_start(radio, False, False, 0)

            row.pack_start(_make_color_swatch(info["bg"]), False, False, 0)
            row.pack_start(_make_color_swatch(info["accent"]), False, False, 0)
            row.pack_start(_make_color_swatch(info["diff_add"]), False, False, 0)

            label_text = info["label"]
            if not matches_system:
                label_text += "  (doesn't match your system mode)"
            label = Gtk.Label(label=label_text)
            label.set_sensitive(matches_system)
            row.pack_start(label, False, False, 0)

            self.pack_start(row, False, False, 0)

        self.show_all()

    def _make_toggle_handler(self, key):
        def handler(radio):
            if radio.get_active():
                self.selected_palette = key
                self.on_selected(key)
        return handler
