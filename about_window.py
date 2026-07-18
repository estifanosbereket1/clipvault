import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf
import os

GITHUB_URL = "https://github.com/estifanosbereket1/clipvault"


def get_app_version() -> str:
    try:
        with open("VERSION", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"


class AboutWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="About ClipVault")
        self.set_default_size(380, 460)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer.set_border_width(0)
        self.add(outer)

        # --- Header band with logo, visually separated from the rest ---
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        header.set_border_width(28)
        header.get_style_context().add_class("about-header")

        logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "assets", "icons", "app-icon.png"
        )
        if os.path.exists(logo_path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 88, 88, True)
            logo = Gtk.Image.new_from_pixbuf(pixbuf)
            logo.set_halign(Gtk.Align.CENTER)
            header.pack_start(logo, False, False, 0)

        title = Gtk.Label()
        title.set_markup("<span size='xx-large' weight='bold'>ClipVault</span>")
        title.set_halign(Gtk.Align.CENTER)
        header.pack_start(title, False, False, 0)

        tagline = Gtk.Label(label="Your clipboard, everywhere. Never in the cloud.")
        tagline.get_style_context().add_class("dim-label")
        tagline.set_halign(Gtk.Align.CENTER)
        header.pack_start(tagline, False, False, 0)

        outer.pack_start(header, False, False, 0)

        # --- Body ---
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_border_width(24)

        version_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        version_row.set_halign(Gtk.Align.CENTER)
        version_badge = Gtk.Label(label=f"v{get_app_version()}")
        version_badge.get_style_context().add_class("version-badge")
        version_row.pack_start(version_badge, False, False, 0)
        body.pack_start(version_row, False, False, 0)

        description = Gtk.Label(
            label="A clipboard manager with QR-to-phone sync, LAN peer sync, "
                  "search, diffing, and more , built to keep your data on "
                  "your own devices."
        )
        description.set_line_wrap(True)
        description.set_justify(Gtk.Justification.CENTER)
        body.pack_start(description, False, False, 4)

        body.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 8)

        creator_label = Gtk.Label()
        creator_label.set_markup("Created with care by <b>Estifanos</b>")
        creator_label.set_halign(Gtk.Align.CENTER)
        body.pack_start(creator_label, False, False, 0)

        links_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        links_box.set_halign(Gtk.Align.CENTER)

        github_button = Gtk.LinkButton.new_with_label(GITHUB_URL, "View source on GitHub")
        links_box.pack_start(github_button, False, False, 0)

        star_button = Gtk.LinkButton.new_with_label(
            GITHUB_URL, "⭐ Star this project if you like it!"
        )
        links_box.pack_start(star_button, False, False, 0)

        body.pack_start(links_box, False, False, 10)

        outer.pack_start(body, True, True, 0)

        self._apply_local_css()
        self.show_all()

    def _apply_local_css(self):
        css = b"""
        .about-header {
            background-color: alpha(@theme_selected_bg_color, 0.08);
            border-bottom: 1px solid alpha(@theme_fg_color, 0.1);
        }
        .version-badge {
            background-color: alpha(@theme_selected_bg_color, 0.15);
            border-radius: 10px;
            padding: 2px 10px;
            font-size: small;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


def _standalone_test():
    win = AboutWindow()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
