import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk

from gnome_shortcuts import (
    find_shortcut_by_name,
    is_combo_taken,
    register_custom_shortcut,
)

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

        self.show_all()
        self.grab_focus()

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


def _standalone_test():
    win = SettingsWindow()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
