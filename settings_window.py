import gi

from qr_popup import generate_qr_for_url

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gdk, GdkPixbuf, Gtk

from gnome_shortcuts import (
    find_shortcut_by_name,
    is_combo_taken,
    register_custom_shortcut,
)
from settings_store import load_settings, save_settings

SHORTCUT_NAME = "Open ClipQR"
SHORTCUT_COMMAND = "kill -SIGUSR1 $(cat /tmp/clipqr.pid)"


class SettingsWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="ClipQR Settings")
        self.set_default_size(360, 220)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)

        # So the window actually receives key-press-event
        self.set_can_focus(True)
        self.connect("key-press-event", self.on_key_press)

        self.captured_accelerator = None

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_border_width(20)
        self.add(outer)

        self.instructions_label = Gtk.Label(
            label="Click the field below, then press your desired\nkey combination for opening ClipQR."
        )
        self.instructions_label.set_justify(Gtk.Justification.CENTER)
        outer.pack_start(self.instructions_label, False, False, 0)

        existing = find_shortcut_by_name(SHORTCUT_NAME)
        self.current_binding = existing[1] if existing else None
        current_text = (
            f"Currently set to: {self.current_binding}"
            if self.current_binding
            else "No shortcut set yet."
        )
        self.current_label = Gtk.Label(label=current_text)
        outer.pack_start(self.current_label, False, False, 0)

        self.capture_label = Gtk.Label(label="Press a key combo...")
        self.capture_label.set_name("capture-label")
        self.capture_label.get_style_context().add_class("capture-box")
        outer.pack_start(self.capture_label, False, False, 0)

        self.status_label = Gtk.Label(label="")
        outer.pack_start(self.status_label, False, False, 0)

        self.save_button = Gtk.Button(label="Save Shortcut")
        self.save_button.set_sensitive(False)
        self.save_button.connect("clicked", self.on_save_clicked)
        outer.pack_start(self.save_button, False, False, 0)

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        outer.pack_start(separator, False, False, 10)

        app_settings = load_settings()

        # History limit
        history_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        history_row.pack_start(Gtk.Label(label="History limit:"), False, False, 0)
        history_adj = Gtk.Adjustment(
            value=app_settings["history_limit"], lower=1, upper=1000, step_increment=1
        )
        self.history_spin = Gtk.SpinButton()
        self.history_spin.set_adjustment(history_adj)
        history_row.pack_start(self.history_spin, False, False, 0)
        outer.pack_start(history_row, False, False, 0)

        # Poll interval
        poll_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        poll_row.pack_start(Gtk.Label(label="Poll interval (sec):"), False, False, 0)
        poll_adj = Gtk.Adjustment(
            value=app_settings["poll_interval"], lower=0.2, upper=10, step_increment=0.1
        )
        self.poll_spin = Gtk.SpinButton()
        self.poll_spin.set_adjustment(poll_adj)
        self.poll_spin.set_digits(1)  # allow one decimal place
        poll_row.pack_start(self.poll_spin, False, False, 0)
        outer.pack_start(poll_row, False, False, 0)

        # Port
        port_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        port_row.pack_start(Gtk.Label(label="Server port:"), False, False, 0)
        port_adj = Gtk.Adjustment(
            value=app_settings["port"], lower=1024, upper=65535, step_increment=1
        )
        self.port_spin = Gtk.SpinButton()
        self.port_spin.set_adjustment(port_adj)
        port_row.pack_start(self.port_spin, False, False, 0)
        outer.pack_start(port_row, False, False, 0)

        # Save button + status
        self.settings_status_label = Gtk.Label(label="")
        outer.pack_start(self.settings_status_label, False, False, 0)

        save_settings_button = Gtk.Button(label="Save Settings")
        save_settings_button.connect("clicked", self.on_save_settings_clicked)
        outer.pack_start(save_settings_button, False, False, 0)

        ca_instructions = Gtk.Label(
            label=(
                "To let a new phone auto-copy from QR codes, scan this to download\n"
                "the certificate, then go to:\n"
                "Settings → Security → Encryption & credentials → Install a certificate\n"
                "→ CA certificate, and select the downloaded file."
            )
        )
        ca_instructions.set_justify(Gtk.Justification.CENTER)
        outer.pack_start(ca_instructions, False, False, 0)

        ca_qr_button = Gtk.Button(label="Show CA Setup QR")
        ca_qr_button.connect("clicked", self.on_show_ca_qr_clicked)
        outer.pack_start(ca_qr_button, False, False, 0)

        self.show_all()
        self.grab_focus()

    def on_show_ca_qr_clicked(self, _button):
        settings = load_settings()
        url = f"https://{settings['last_known_ip']}:{settings['port']}/setup-ca"
        image_path = generate_qr_for_url(url, "ca-setup")

        popup = Gtk.Window(title="Scan to trust ClipQR on this device")
        popup.set_default_size(320, 360)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, 280, 280, True)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        popup.add(image)
        popup.show_all()

    def on_save_settings_clicked(self, _button):
        new_values = {
            "history_limit": self.history_spin.get_value_as_int(),
            "poll_interval": round(self.poll_spin.get_value(), 1),
            "port": self.port_spin.get_value_as_int(),
        }
        errors = save_settings(new_values)
        if errors:
            self.settings_status_label.set_text("\n".join(errors))
        else:
            self.settings_status_label.set_text(
                "Saved. Poll interval and port changes require an app restart."
            )

    def on_key_press(self, _widget, event):
        # Ignore lone modifier presses (Ctrl/Alt/Shift/Super by themselves) --
        # we only want to capture once a real key is pressed alongside them.
        modifier_keyvals = (
            Gdk.KEY_Control_L,
            Gdk.KEY_Control_R,
            Gdk.KEY_Alt_L,
            Gdk.KEY_Alt_R,
            Gdk.KEY_Shift_L,
            Gdk.KEY_Shift_R,
            Gdk.KEY_Super_L,
            Gdk.KEY_Super_R,
        )
        if event.keyval in modifier_keyvals:
            return True

        accelerator = Gtk.accelerator_name(
            event.keyval, event.state & Gtk.accelerator_get_default_mod_mask()
        )
        self.captured_accelerator = accelerator
        self.capture_label.set_text(accelerator)

        conflict = is_combo_taken(accelerator)
        if conflict and accelerator == self.current_binding:
            conflict = None  # it's just our own existing binding, not a real conflict

        if conflict:
            self.status_label.set_text(f"Already used by: {conflict}")
            self.save_button.set_sensitive(False)
        else:
            self.status_label.set_text("Available")
            self.save_button.set_sensitive(True)

        return True  # stop this key event from propagating further

    def on_save_clicked(self, _button):
        if not self.captured_accelerator:
            return

        register_custom_shortcut(
            name=SHORTCUT_NAME,
            shell_command=SHORTCUT_COMMAND,
            accelerator=self.captured_accelerator,
        )
        self.status_label.set_text(f"Saved: {self.captured_accelerator}")
        self.current_binding = self.captured_accelerator
        self.current_label.set_text(f"Currently set to: {self.current_binding}")
        self.save_button.set_sensitive(False)


def on_show_ca_qr_clicked(self, _button):
    settings = load_settings()
    url = f"https://{settings['last_known_ip']}:{settings['port']}/setup-ca"
    image_path = generate_qr_for_url(url, "ca-setup")

    popup = Gtk.Window(title="Scan to trust ClipQR on this device")
    popup.set_default_size(320, 360)
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, 280, 280, True)
    image = Gtk.Image.new_from_pixbuf(pixbuf)
    popup.add(image)
    popup.show_all()


def _standalone_test():
    win = SettingsWindow()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
