import gi

from qr_popup import generate_qr_for_url

from palette_picker import PalettePicker
from theme_manager import get_system_theme_is_dark

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gdk, GdkPixbuf, Gtk

from gnome_shortcuts import (
    find_shortcut_by_name,
    is_combo_taken,
    register_custom_shortcut,
)
from settings_store import load_settings, save_settings

SHORTCUT_NAME = "Open ClipVault"
SHORTCUT_COMMAND = "kill -SIGUSR1 $(cat /tmp/clipvault.pid)"


class SettingsWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="ClipVault Settings")
        self.set_default_size(420, 560)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.set_can_focus(True)
        self.connect("key-press-event", self.on_key_press)

        self.captured_accelerator = None

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.add(scrolled)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_border_width(20)
        scrolled.add(outer)

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
        history_label = Gtk.Label(label="History limit:")
        history_label.set_xalign(0)
        history_label.set_hexpand(True)
        history_row.pack_start(history_label, True, True, 0)
        history_adj = Gtk.Adjustment(
            value=app_settings["history_limit"], lower=1, upper=1000, step_increment=1
        )
        self.history_spin = Gtk.SpinButton()
        self.history_spin.set_adjustment(history_adj)
        history_row.pack_end(self.history_spin, False, False, 0)
        outer.pack_start(history_row, False, False, 0)

        # Poll interval
        poll_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        poll_label = Gtk.Label(label="Poll interval (sec):")
        poll_label.set_xalign(0)
        poll_label.set_hexpand(True)
        poll_row.pack_start(poll_label, True, True, 0)
        poll_adj = Gtk.Adjustment(
            value=app_settings["poll_interval"], lower=0.2, upper=10, step_increment=0.1
        )
        self.poll_spin = Gtk.SpinButton()
        self.poll_spin.set_adjustment(poll_adj)
        self.poll_spin.set_digits(1)
        poll_row.pack_end(self.poll_spin, False, False, 0)
        outer.pack_start(poll_row, False, False, 0)

        # Port
        port_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        port_label = Gtk.Label(label="Server port:")
        port_label.set_xalign(0)
        port_label.set_hexpand(True)
        port_row.pack_start(port_label, True, True, 0)
        port_adj = Gtk.Adjustment(
            value=app_settings["port"], lower=1024, upper=65535, step_increment=1
        )
        self.port_spin = Gtk.SpinButton()
        self.port_spin.set_adjustment(port_adj)
        port_row.pack_end(self.port_spin, False, False, 0)
        outer.pack_start(port_row, False, False, 0)

        # Playback mode
        playback_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        playback_label = Gtk.Label(label="Playback mode:")
        playback_label.set_xalign(0)
        playback_label.set_hexpand(True)
        playback_row.pack_start(playback_label, True, True, 0)

        self.playback_combo = Gtk.ComboBoxText()
        self.playback_combo.append("time", "Visual timeline (fun)")
        self.playback_combo.append("index", "Simple slider")
        self.playback_combo.set_active_id(app_settings.get("playback_mode", "time"))
        playback_row.pack_end(self.playback_combo, False, False, 0)
        outer.pack_start(playback_row, False, False, 0)

        system_is_dark = get_system_theme_is_dark()
        current_key = "dark_palette" if system_is_dark else "light_palette"
        current_palette = app_settings.get(current_key, "midnight" if system_is_dark else "daylight")

        self.palette_picker = PalettePicker(
            current_palette=current_palette,
            on_selected=lambda key: None,
        )
        outer.pack_start(self.palette_picker, False, False, 0)

        # self.palette_picker = PalettePicker(
        #     current_palette=app_settings.get("palette", "midnight"),
        #     on_selected=lambda key: None,
        # )
        # outer.pack_start(self.palette_picker, False, False, 0)

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

        send_qr_button = Gtk.Button(label="Show 'Send from Phone' QR")
        send_qr_button.connect("clicked", self.on_show_send_qr_clicked)
        outer.pack_start(send_qr_button, False, False, 0)

        ca_qr_button = Gtk.Button(label="Show CA Setup QR")
        ca_qr_button.connect("clicked", self.on_show_ca_qr_clicked)
        outer.pack_start(ca_qr_button, False, False, 0)

        self.show_all()
        self.grab_focus()

    def on_show_send_qr_clicked(self, _button):
        settings = load_settings()
        url = f"https://{settings['last_known_ip']}:{settings['port']}/send"
        image_path = generate_qr_for_url(url, "send-from-phone")

        popup = Gtk.Window(title="Scan to send from your phone")
        popup.set_default_size(320, 380)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_border_width(16)

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, 280, 280, True)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        box.pack_start(image, True, True, 0)

        hint = Gtk.Label(
            label="After scanning, use your browser's \"Add to Home Screen\" "
                  "option to install this as an app for quick access later."
        )
        hint.set_line_wrap(True)
        hint.set_justify(Gtk.Justification.CENTER)
        hint.set_margin_top(10)
        box.pack_start(hint, False, False, 0)

        popup.add(box)
        popup.show_all()

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
            "playback_mode": self.playback_combo.get_active_id(),
            self.palette_picker.settings_key: self.palette_picker.selected_palette,
        }
        errors = save_settings(new_values)
        if errors:
            self.settings_status_label.set_text("\n".join(errors))
        else:
            from theme_manager import apply_theme_for_current_system_mode
            apply_theme_for_current_system_mode()
            self.settings_status_label.set_text(
                "Saved. Poll interval and port changes require an app restart."
            )

    # def on_save_settings_clicked(self, _button):
    #     new_values = {
    #         "history_limit": self.history_spin.get_value_as_int(),
    #         "poll_interval": round(self.poll_spin.get_value(), 1),
    #         "port": self.port_spin.get_value_as_int(),
    #         "playback_mode": self.playback_combo.get_active_id(),
    #         "palette": self.palette_picker.selected_palette,
    #     }
    #     errors = save_settings(new_values)
    #     if errors:
    #         self.settings_status_label.set_text("\n".join(errors))
    #     else:
    #         from theme_manager import apply_theme
    #         apply_theme(new_values["palette"])
    #         self.settings_status_label.set_text(
    #             "Saved. Poll interval and port changes require an app restart."
    #         )

    def on_key_press(self, _widget, event):
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
            conflict = None

        if conflict:
            self.status_label.set_text(f"Already used by: {conflict}")
            self.save_button.set_sensitive(False)
        else:
            self.status_label.set_text("Available")
            self.save_button.set_sensitive(True)

        return True

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


def _standalone_test():
    win = SettingsWindow()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
