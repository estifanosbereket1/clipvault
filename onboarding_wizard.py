import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from settings_store import save_settings
from gi.repository import Gtk, GdkPixbuf, GLib


class OnboardingWizard(Gtk.Window):
    def __init__(self, on_complete):
        """
        on_complete: called with no arguments once the user finishes the
        wizard (after settings are saved and onboarded=True is set).
        """
        super().__init__(title="Welcome to ClipQR")
        self.on_complete = on_complete
        self.set_default_size(480, 420)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)

        self.set_can_focus(True)
        self.connect("key-press-event", self.on_wizard_key_press)

        self.step_names = ["welcome", "theme", "port", "hotkey", "done"]
        self.current_step_index = 0

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_border_width(20)
        self.add(outer)

        self.step_indicator = Gtk.Label(label="")
        self.step_indicator.get_style_context().add_class("dim-label")
        outer.pack_start(self.step_indicator, False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(150)
        outer.pack_start(self.stack, True, True, 0)

        self._build_welcome_page()
        # self._build_placeholder_page("theme", "Theme step coming soon")
        self._build_theme_page()
        # self._build_placeholder_page("port", "Port step coming soon")
        self._build_port_page()
        # self._build_placeholder_page("hotkey", "Hotkey step coming soon")
        self._build_hotkey_page()
        # self._build_placeholder_page("done", "Done step coming soon")
        self._build_done_page()

        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.back_button = Gtk.Button(label="Back")
        self.back_button.connect("clicked", self.on_back_clicked)
        self.next_button = Gtk.Button(label="Next")
        self.next_button.connect("clicked", self.on_next_clicked)
        nav_box.pack_start(self.back_button, False, False, 0)
        nav_box.pack_end(self.next_button, False, False, 0)
        outer.pack_start(nav_box, False, False, 0)

        self._update_step_ui()
        self.show_all()

    def _build_welcome_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_border_width(10)

        from icon_loader import load_icon
        import os

        logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "assets", "icons", "app-icon.png"
        )
        if os.path.exists(logo_path):
            logo_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 72, 72, True)
            logo_image = Gtk.Image.new_from_pixbuf(logo_pixbuf)
            logo_image.set_halign(Gtk.Align.CENTER)
            page.pack_start(logo_image, False, False, 6)

        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Welcome to ClipQR</span>")
        title.set_halign(Gtk.Align.CENTER)
        page.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label="Your clipboard, everywhere.")
        subtitle.get_style_context().add_class("dim-label")
        subtitle.set_halign(Gtk.Align.CENTER)
        page.pack_start(subtitle, False, False, 4)

        page.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 10)

        features = [
            ("qr-code", "Scan a QR code to copy any entry straight to your phone"),
            ("git-compare", "Sync clipboard history with other devices on your network"),
            ("star", "Pin, search, and diff your history automatically"),
        ]

        for icon_name, text in features:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.pack_start(load_icon(icon_name, size=20), False, False, 0)
            label = Gtk.Label(label=text)
            label.set_line_wrap(True)
            label.set_xalign(0)
            row.pack_start(label, True, True, 0)
            page.pack_start(row, False, False, 4)

        footer = Gtk.Label(label="This quick setup takes under a minute.")
        footer.get_style_context().add_class("dim-label")
        footer.set_halign(Gtk.Align.CENTER)
        page.pack_start(footer, False, False, 14)

        self.stack.add_named(page, "welcome")

    def _build_done_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_border_width(10)
        self.stack.add_named(page, "done")

    # def _build_done_page(self):
    #     from icon_loader import load_icon

    #     page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    #     page.set_border_width(10)

    #     check_icon = load_icon("copy", size=48)  # placeholder; swap for a checkmark icon once you have one
    #     check_icon.set_halign(Gtk.Align.CENTER)
    #     page.pack_start(check_icon, False, False, 10)

    #     title = Gtk.Label()
    #     title.set_markup("<span size='x-large' weight='bold'>You're all set!</span>")
    #     title.set_halign(Gtk.Align.CENTER)
    #     page.pack_start(title, False, False, 0)

    #     summary = Gtk.Label(label=self._build_summary_text())
    #     summary.set_line_wrap(True)
    #     summary.set_xalign(0)
    #     page.pack_start(summary, False, False, 10)

    #     self.stack.add_named(page, "done")

    def _build_summary_text(self):
        theme_name = self.theme_picker.selected_palette.title() if hasattr(self, "theme_picker") else "default"
        port = self.selected_port if self.selected_port else "default"
        hotkey = self.captured_hotkey_accelerator or "not set (can be added later in Settings)"

        return (
            f"Theme: {theme_name}\n"
            f"Port: {port}\n"
            f"Hotkey: {hotkey}\n\n"
            "Click \"Get Started\" to open your clipboard history."
        )

    def _build_hotkey_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_border_width(10)

        title = Gtk.Label()
        title.set_markup("<span size='large' weight='bold'>Set your hotkey</span>")
        title.set_halign(Gtk.Align.START)
        page.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(
            label="Click below, then press a key combination to open ClipQR from anywhere."
        )
        subtitle.get_style_context().add_class("dim-label")
        subtitle.set_line_wrap(True)
        subtitle.set_halign(Gtk.Align.START)
        page.pack_start(subtitle, False, False, 6)

        self.hotkey_capture_label = Gtk.Label(label="Press a key combo...")
        self.hotkey_capture_label.get_style_context().add_class("capture-box")
        page.pack_start(self.hotkey_capture_label, False, False, 10)

        self.hotkey_status_label = Gtk.Label(label="")
        page.pack_start(self.hotkey_status_label, False, False, 0)

        skip_note = Gtk.Label(
            label="You can also set this later from Settings."
        )
        skip_note.get_style_context().add_class("dim-label")
        page.pack_start(skip_note, False, False, 10)

        self.captured_hotkey_accelerator = None

        self.stack.add_named(page, "hotkey")

    def on_wizard_key_press(self, _widget, event):
        if self.step_names[self.current_step_index] != "hotkey":
            return False  # only capture keys while on the hotkey step

        from gi.repository import Gdk
        from gnome_shortcuts import is_combo_taken

        modifier_keyvals = (
            Gdk.KEY_Control_L, Gdk.KEY_Control_R,
            Gdk.KEY_Alt_L, Gdk.KEY_Alt_R,
            Gdk.KEY_Shift_L, Gdk.KEY_Shift_R,
            Gdk.KEY_Super_L, Gdk.KEY_Super_R,
        )
        if event.keyval in modifier_keyvals:
            return True

        accelerator = Gtk.accelerator_name(
            event.keyval, event.state & Gtk.accelerator_get_default_mod_mask()
        )
        self.captured_hotkey_accelerator = accelerator
        self.hotkey_capture_label.set_text(accelerator)

        conflict = is_combo_taken(accelerator)
        if conflict:
            self.hotkey_status_label.set_text(f"Already used by: {conflict}")
        else:
            self.hotkey_status_label.set_text("Available")

        return True

    def _build_placeholder_page(self, name, text):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(label=text)
        page.pack_start(label, True, True, 0)
        self.stack.add_named(page, name)

    def _build_theme_page(self):
        from palette_picker import PalettePicker
        from theme_manager import apply_theme

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_border_width(10)

        title = Gtk.Label()
        title.set_markup("<span size='large' weight='bold'>Choose your theme</span>")
        title.set_halign(Gtk.Align.START)
        page.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(
            label="Pick a palette that matches your system's dark or light mode."
        )
        subtitle.get_style_context().add_class("dim-label")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_line_wrap(True)
        page.pack_start(subtitle, False, False, 6)

        self.theme_picker = PalettePicker(
            current_palette=self._get_default_palette_for_system(),
            on_selected=lambda key: apply_theme(key),  # live preview as they click
        )
        page.pack_start(self.theme_picker, False, False, 0)

        self.stack.add_named(page, "theme")

    def _build_port_page(self):
        from port_checker import get_available_ports

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_border_width(10)

        title = Gtk.Label()
        title.set_markup("<span size='large' weight='bold'>Choose a port</span>")
        title.set_halign(Gtk.Align.START)
        page.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(
            label="This is used for the local HTTPS server that lets your phone auto-copy via QR codes."
        )
        subtitle.get_style_context().add_class("dim-label")
        subtitle.set_line_wrap(True)
        subtitle.set_halign(Gtk.Align.START)
        page.pack_start(subtitle, False, False, 6)

        checking_label = Gtk.Label(label="Checking available ports...")
        page.pack_start(checking_label, False, False, 10)

        self.selected_port = None
        self.port_radio_group = None

        def do_check():
            available = get_available_ports(limit=4)
            checking_label.destroy()

            if not available:
                fallback = Gtk.Label(
                    label="Couldn't find a free port automatically. Enter one manually below."
                )
                fallback.set_line_wrap(True)
                page.pack_start(fallback, False, False, 6)
            else:
                self.selected_port = available[0]
                for port in available:
                    row = Gtk.RadioButton.new_with_label_from_widget(
                        self.port_radio_group, f"Port {port} (available)"
                    )
                    if self.port_radio_group is None:
                        self.port_radio_group = row
                    row.set_active(port == self.selected_port)
                    row.connect("toggled", self._make_port_radio_handler(port))
                    page.pack_start(row, False, False, 2)

            manual_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            manual_row.pack_start(Gtk.Label(label="Or enter your own:"), False, False, 0)
            self.manual_port_entry = Gtk.Entry()
            self.manual_port_entry.set_placeholder_text("e.g. 8000")
            self.manual_port_entry.connect("changed", self._on_manual_port_changed)
            manual_row.pack_start(self.manual_port_entry, False, False, 0)
            page.pack_start(manual_row, False, False, 10)

            self.port_status_label = Gtk.Label(label="")
            page.pack_start(self.port_status_label, False, False, 0)

            page.show_all()

        GLib.idle_add(do_check)

        self.stack.add_named(page, "port")

    def _make_port_radio_handler(self, port):
        def handler(radio):
            if radio.get_active():
                self.selected_port = port
                self.manual_port_entry.set_text("")
        return handler

    def _on_manual_port_changed(self, entry):
        from port_checker import is_port_available

        text = entry.get_text().strip()
        if not text:
            return

        if not text.isdigit():
            self.port_status_label.set_text("Port must be a number.")
            return

        port = int(text)
        if not (1024 <= port <= 65535):
            self.port_status_label.set_text("Port must be between 1024 and 65535.")
            return

        if is_port_available(port):
            self.selected_port = port
            self.port_status_label.set_text(f"Port {port} is available.")
            if self.port_radio_group:
                for radio in self.port_radio_group.get_group():
                    radio.set_active(False)
        else:
            self.port_status_label.set_text(f"Port {port} is already in use.")

    def _get_default_palette_for_system(self):
        from theme_manager import get_system_theme_is_dark
        return "midnight" if get_system_theme_is_dark() else "daylight"

    def _refresh_done_page(self):
        done_page = self.stack.get_child_by_name("done")
        for child in done_page.get_children():
            child.destroy()

        from icon_loader import load_icon

        check_icon = load_icon("copy", size=48)
        check_icon.set_halign(Gtk.Align.CENTER)
        done_page.pack_start(check_icon, False, False, 10)

        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>You're all set!</span>")
        title.set_halign(Gtk.Align.CENTER)
        done_page.pack_start(title, False, False, 0)

        summary = Gtk.Label(label=self._build_summary_text())
        summary.set_line_wrap(True)
        summary.set_xalign(0)
        done_page.pack_start(summary, False, False, 10)

        done_page.show_all()

    def _update_step_ui(self):
        step_name = self.step_names[self.current_step_index]
        if step_name == "done":
                self._refresh_done_page()

        self.stack.set_visible_child_name(step_name)
        self.step_indicator.set_text(
            f"Step {self.current_step_index + 1} of {len(self.step_names)}"
        )
        self.back_button.set_sensitive(self.current_step_index > 0)

        is_last_step = self.current_step_index == len(self.step_names) - 1
        self.next_button.set_label("Get Started" if is_last_step else "Next")

    def on_back_clicked(self, _button):
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self._update_step_ui()

    def on_next_clicked(self, _button):
        is_last_step = self.current_step_index == len(self.step_names) - 1
        if is_last_step:
            self._finish()
            return
        self.current_step_index += 1
        self._update_step_ui()

    def _finish(self):
        from gnome_shortcuts import register_custom_shortcut

        save_settings({
            "onboarded": True,
            self.theme_picker.settings_key: self.theme_picker.selected_palette,
            "port": self.selected_port,
        })

        if self.captured_hotkey_accelerator:
            register_custom_shortcut(
                name="Open ClipVault",
                shell_command="kill -SIGUSR1 $(cat /tmp/clipvault.pid)",
                accelerator=self.captured_hotkey_accelerator,
            )

        self.destroy()
        if self.on_complete:
            self.on_complete()


def _standalone_test():
    def on_complete():
        print("Onboarding complete!")
        Gtk.main_quit()

    win = OnboardingWizard(on_complete=on_complete)
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
