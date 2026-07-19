import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk, Gdk, Gio

from palettes import get_palette

_current_provider = None


def build_css(palette: dict) -> str:
    return f"""
    window {{
        background-color: {palette['bg']};
        color: {palette['text']};
    }}

    label {{
        color: {palette['text']};
    }}

    label.dim-label {{
        color: {palette['muted']};
    }}

    button {{
        background-color: {palette['surface']};
        background-image: none;
        color: {palette['text']};
        border: 1px solid {palette['border']};
        border-radius: 6px;
        outline: none;
        box-shadow: none;
    }}

    button.tag-chip {{
        background-color: {palette['surface']};
        border: 1px solid {palette['accent']};
        color: {palette['accent']};
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 11px;
        min-height: 0;
    }}
    button.tag-chip-add {{
        background-color: transparent;
        border: 1px dashed {palette['border']};
        color: {palette['muted']};
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 11px;
        min-height: 0;
    }}

    button:hover {{
        background-color: {palette['border']};
        background-image: none;
    }}

    button:focus {{
        outline: none;
        box-shadow: none;
        border: 1px solid {palette['accent']};
    }}

    entry {{
        background-color: {palette['surface']};
        color: {palette['text']};
        border: 2px solid {palette['accent']};
        border-radius: 4px;
        padding: 4px 8px;
    }}

    label.secret-warning-label {{
        color: {palette['error']};
        font-weight: 600;
    }}

    scrolledwindow, list, row {{
        background-color: {palette['bg']};
    }}

    row:hover {{
        background-color: {palette['surface']};
    }}

    separator {{
        background-color: {palette['border']};
    }}
    menuitem.uninstall-menu-item label {{
        color: {palette['error']};
    }}
    """


def apply_theme(palette_name: str):
    """
    Loads and applies the given palette's CSS globally across the whole app.
    Safe to call again later to switch palettes live -- replaces the
    previously active provider rather than stacking multiple providers.
    """
    global _current_provider

    palette = get_palette(palette_name)
    css = build_css(palette)

    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode("utf-8"))

    screen = Gdk.Screen.get_default()

    if _current_provider is not None:
        Gtk.StyleContext.remove_provider_for_screen(screen, _current_provider)

    Gtk.StyleContext.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    _current_provider = provider


def get_system_theme_is_dark() -> bool:
    """
    Returns whether the system's GTK/GNOME theme is currently dark, so we
    can warn the user if their chosen palette's brightness would clash with
    the OS-drawn window titlebar (which follows the system theme, not ours).
    """
    try:
        settings = Gio.Settings.new("org.gnome.desktop.interface")
        color_scheme = settings.get_string("color-scheme")
        return color_scheme == "prefer-dark"
    except Exception:
        return True  # reasonable fallback given most Linux dev setups default dark

def apply_theme_for_current_system_mode():
    """
    Reads the saved dark/light palette preference matching the current
    system mode, and applies it.
    """
    from settings_store import load_settings

    settings = load_settings()
    system_is_dark = get_system_theme_is_dark()
    palette_name = settings["dark_palette"] if system_is_dark else settings["light_palette"]
    apply_theme(palette_name)

def get_active_palette() -> dict:
    """
    Returns the full palette dict currently in effect, based on the saved
    per-mode preference and the system's current dark/light state. Useful
    for any widget that needs actual color values in Python (not just CSS),
    like Gtk.TextTag colors which CSS providers don't control.
    """
    from settings_store import load_settings
    from palettes import get_palette

    settings = load_settings()
    system_is_dark = get_system_theme_is_dark()
    palette_name = settings["dark_palette"] if system_is_dark else settings["light_palette"]
    return get_palette(palette_name)


def watch_system_theme_changes():
    """
    Listens for the system dark/light mode changing live, and automatically
    re-applies the correct saved palette when it does. Returns the Gio.Settings
    object -- keep a reference to it so the signal connection isn't garbage collected.
    """
    settings = Gio.Settings.new("org.gnome.desktop.interface")
    settings.connect("changed::color-scheme", lambda *_args: apply_theme_for_current_system_mode())
    return settings


def _standalone_test():
    win = Gtk.Window(title="Theme Test")
    win.set_default_size(300, 200)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    box.set_border_width(20)
    win.add(box)

    label = Gtk.Label(label="Sample text")
    box.pack_start(label, False, False, 0)

    dim_label = Gtk.Label(label="Muted text")
    dim_label.get_style_context().add_class("dim-label")
    box.pack_start(dim_label, False, False, 0)

    button = Gtk.Button(label="Sample Button")
    box.pack_start(button, False, False, 0)

    entry = Gtk.Entry()
    box.pack_start(entry, False, False, 0)

    apply_theme("forest")

    print("System theme is dark:", get_system_theme_is_dark())

    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
