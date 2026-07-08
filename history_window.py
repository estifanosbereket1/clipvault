# import gi
# import pyperclip

# gi.require_version("Gtk", "3.0")
# from gi.repository import GLib, Gtk

# from qr_display import QrPopup
# from settings_store import load_settings
# from storage import add_entry, delete_entry, get_history


# def truncate(text: str, max_len: int = 60) -> str:
#     """Shorten long clipboard text for display in the list."""
#     text = text.replace("\n", " ")
#     if len(text) > max_len:
#         return text[:max_len].rstrip() + "..."
#     return text


# class HistoryWindow(Gtk.Window):
#     def __init__(self, on_qr_clicked=None):
#         """
#         on_qr_clicked: a function you provide, called as on_qr_clicked(entry)
#         whenever the user clicks the QR button on a row. `entry` is the
#         sqlite3.Row for that clipboard item (has entry["id"], entry["content"], etc).
#         """
#         super().__init__(title="Clipboard History")
#         self.on_qr_clicked = on_qr_clicked

#         self.set_default_size(420, 480)
#         self.set_position(Gtk.WindowPosition.CENTER)

#         # Close the window instead of destroying the app when the X is clicked,
#         # so we can reopen it later from the tray/hotkey without recreating it.
#         self.connect("delete-event", self.on_delete_event)

#         outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
#         outer_box.set_border_width(8)
#         self.add(outer_box)

#         # Header row: title + refresh button
#         header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
#         title_label = Gtk.Label(label="Clipboard History")
#         title_label.set_xalign(0)
#         title_label.set_hexpand(True)
#         refresh_btn = Gtk.Button(label="Refresh")
#         refresh_btn.connect("clicked", lambda _btn: self.refresh())
#         header.pack_start(title_label, True, True, 0)
#         header.pack_end(refresh_btn, False, False, 0)
#         outer_box.pack_start(header, False, False, 0)

#         # Scrollable list
#         scrolled = Gtk.ScrolledWindow()
#         scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
#         scrolled.set_vexpand(True)
#         outer_box.pack_start(scrolled, True, True, 0)

#         self.list_box = Gtk.ListBox()
#         self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
#         scrolled.add(self.list_box)

#         self.refresh()

#     def refresh(self):
#         """Reload entries from storage and rebuild the list."""
#         # Clear existing rows
#         for child in self.list_box.get_children():
#             self.list_box.remove(child)

#         entries = get_history(limit=load_settings()["history_limit"])

#         if not entries:
#             empty_label = Gtk.Label(label="No clipboard history yet.")
#             empty_label.set_margin_top(20)
#             self.list_box.add(empty_label)
#         else:
#             for entry in entries:
#                 row = self._build_row(entry)
#                 self.list_box.add(row)

#         self.list_box.show_all()

#     # def _build_row(self, entry) -> Gtk.ListBoxRow:
#     #     """Build a single row: [text preview .......... [QR button]]"""
#     #     row = Gtk.ListBoxRow()
#     #     row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
#     #     row_box.set_margin_top(4)
#     #     row_box.set_margin_bottom(4)
#     #     row_box.set_margin_start(6)
#     #     row_box.set_margin_end(6)

#     #     text_label = Gtk.Label(label=truncate(entry["content"]))
#     #     text_label.set_xalign(0)
#     #     text_label.set_hexpand(True)
#     #     text_label.set_ellipsize(
#     #         3
#     #     )  # Pango.EllipsizeMode.END, avoids importing Pango just for this

#     #     qr_button = Gtk.Button(label="QR")
#     #     qr_button.set_tooltip_text("Show QR code for this entry")
#     #     qr_button.connect("clicked", self._make_qr_handler(entry))

#     #     row_box.pack_start(text_label, True, True, 0)
#     #     row_box.pack_end(qr_button, False, False, 0)

#     #     row.add(row_box)
#     #     return row
#     def _confirm_delete(self, entry) -> bool:
#         dialog = Gtk.MessageDialog(
#             transient_for=self,
#             flags=0,
#             message_type=Gtk.MessageType.WARNING,
#             buttons=Gtk.ButtonsType.YES_NO,
#             text="Delete this entry?",
#         )
#         dialog.format_secondary_text(truncate(entry["content"], max_len=80))
#         response = dialog.run()
#         dialog.destroy()
#         return response == Gtk.ResponseType.YES

#     def _build_row(self, entry) -> Gtk.ListBoxRow:
#         row = Gtk.ListBoxRow()
#         row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
#         row_box.set_margin_top(4)
#         row_box.set_margin_bottom(4)
#         row_box.set_margin_start(6)
#         row_box.set_margin_end(6)

#         text_label = Gtk.Label(label=truncate(entry["content"]))
#         text_label.set_xalign(0)
#         text_label.set_hexpand(True)
#         text_label.set_ellipsize(3)

#         qr_button = self._icon_button("view-grid-symbolic", "Show QR code")
#         qr_button.connect("clicked", self._make_qr_handler(entry))

#         copy_button = self._icon_button("edit-copy-symbolic", "Copy to clipboard")
#         copy_button.connect("clicked", self._make_copy_handler(entry))

#         delete_button = self._icon_button("user-trash-symbolic", "Delete entry")
#         delete_button.connect("clicked", self._make_delete_handler(entry))

#         row_box.pack_start(text_label, True, True, 0)
#         row_box.pack_end(delete_button, False, False, 0)
#         row_box.pack_end(copy_button, False, False, 0)
#         row_box.pack_end(qr_button, False, False, 0)

#         row.add(row_box)
#         return row

#     def _icon_button(self, icon_name, tooltip):
#         button = Gtk.Button()
#         icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
#         button.set_image(icon)
#         button.set_tooltip_text(tooltip)
#         return button

#     def _make_copy_handler(self, entry):
#         def handler(_button):
#             pyperclip.copy(entry["content"])
#             add_entry(entry["content"])
#             self.refresh()

#         return handler

#     def _make_delete_handler(self, entry):
#         def handler(_button):
#             confirmed = self._confirm_delete(entry)
#             if confirmed:
#                 delete_entry(entry["id"])
#                 self.refresh()

#         return handler

#     def _make_qr_handler(self, entry):
#         """Returns a closure so each button knows which entry it belongs to."""

#         def handler(_button):
#             if self.on_qr_clicked:
#                 self.on_qr_clicked(entry)
#             else:
#                 print(f"QR requested for entry id={entry['id']}: {entry['content']!r}")

#         return handler

#     def on_delete_event(self, _widget, _event):
#         """Hide instead of destroy, so tray/hotkey can show it again later."""
#         self.hide()
#         return True  # stops the default destroy behavior

#     def show_window(self):
#         """Call this from your tray icon / hotkey callback to (re)open the window."""
#         self.refresh()
#         self.show_all()
#         self.present()


# def open_qr_popup(entry):
#     QrPopup(entry)


# def _standalone_test():
#     """Quick manual test: opens the window directly, no tray/hotkey needed yet."""
#     win = HistoryWindow(on_qr_clicked=open_qr_popup)
#     win.connect("destroy", Gtk.main_quit)
#     win.show_all()
#     Gtk.main()


# if __name__ == "__main__":
#     _standalone_test()


import gi
import pyperclip

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from qr_display import QrPopup
from settings_store import load_settings
from storage import (
    add_entry,
    delete_entry,
    get_pinned_entries,
    get_recent_unpinned,
    pin_entry,
    unpin_entry,
)


def truncate(text: str, max_len: int = 60) -> str:
    """Shorten long clipboard text for display in the list."""
    text = text.replace("\n", " ")
    if len(text) > max_len:
        return text[:max_len].rstrip() + "..."
    return text


class HistoryWindow(Gtk.Window):
    def __init__(self, on_qr_clicked=None):
        super().__init__(title="Clipboard History")
        self.on_qr_clicked = on_qr_clicked

        self.set_default_size(420, 520)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("delete-event", self.on_delete_event)

        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer_box.set_border_width(8)
        self.add(outer_box)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_label = Gtk.Label(label="Clipboard History")
        title_label.set_xalign(0)
        title_label.set_hexpand(True)
        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", lambda _btn: self.refresh())
        header.pack_start(title_label, True, True, 0)
        header.pack_end(refresh_btn, False, False, 0)
        outer_box.pack_start(header, False, False, 0)

        # --- Pinned section ---
        self.pinned_label = Gtk.Label(label="Pinned")
        self.pinned_label.set_xalign(0)
        self.pinned_label.get_style_context().add_class("dim-label")
        outer_box.pack_start(self.pinned_label, False, False, 0)

        self.pinned_list_box = Gtk.ListBox()
        self.pinned_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        outer_box.pack_start(self.pinned_list_box, False, False, 0)

        outer_box.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4
        )

        # --- Recent section ---
        recent_label = Gtk.Label(label="Recent")
        recent_label.set_xalign(0)
        recent_label.get_style_context().add_class("dim-label")
        outer_box.pack_start(recent_label, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        outer_box.pack_start(scrolled, True, True, 0)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.add(self.list_box)

        self.refresh()

    def refresh(self):
        """Reload entries from storage and rebuild both sections."""
        for child in self.pinned_list_box.get_children():
            self.pinned_list_box.remove(child)
        for child in self.list_box.get_children():
            self.list_box.remove(child)

        pinned_entries = get_pinned_entries()
        if pinned_entries:
            self.pinned_label.show()
            for entry in pinned_entries:
                row = self._build_row(entry, is_pinned=True)
                self.pinned_list_box.add(row)
        else:
            self.pinned_label.hide()

        recent_entries = get_recent_unpinned(limit=load_settings()["history_limit"])
        if not recent_entries:
            empty_label = Gtk.Label(label="No clipboard history yet.")
            empty_label.set_margin_top(20)
            self.list_box.add(empty_label)
        else:
            for entry in recent_entries:
                row = self._build_row(entry, is_pinned=False)
                self.list_box.add(row)

        self.pinned_list_box.show_all()
        self.list_box.show_all()

    def _confirm_delete(self, entry) -> bool:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Delete this entry?",
        )
        dialog.format_secondary_text(truncate(entry["content"], max_len=80))
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.YES

    def _confirm_pin_swap(self, oldest_entry) -> bool:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Pinned list is full (max 5).",
        )
        dialog.format_secondary_text(
            f"Unpin the oldest pinned entry to make room?\n\n{truncate(oldest_entry['content'], max_len=80)}"
        )
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.YES

    def _format_badge(self, content_type):
        if not content_type or content_type == "text":
            return None
        if content_type.startswith("code:"):
            language = content_type.split(":", 1)[1]
            return f"[{language}]"
        return f"[{content_type.upper()}]"

    def _build_row(self, entry, is_pinned: bool) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row_box.set_margin_top(4)
        row_box.set_margin_bottom(4)
        row_box.set_margin_start(6)
        row_box.set_margin_end(6)

        badge_text = self._format_badge(entry["content_type"])
        if badge_text:
            badge_label = Gtk.Label(label=badge_text)
            badge_label.get_style_context().add_class("dim-label")
            row_box.pack_start(badge_label, False, False, 0)

        text_label = Gtk.Label(label=truncate(entry["content"]))
        text_label.set_xalign(0)
        text_label.set_hexpand(True)
        text_label.set_ellipsize(3)

        pin_icon = "starred-symbolic" if is_pinned else "non-starred-symbolic"
        pin_tooltip = "Unpin" if is_pinned else "Pin (max 5)"
        pin_button = self._icon_button(pin_icon, pin_tooltip)
        pin_button.connect("clicked", self._make_pin_handler(entry, is_pinned))

        qr_button = self._icon_button("view-grid-symbolic", "Show QR code")
        qr_button.connect("clicked", self._make_qr_handler(entry))

        copy_button = self._icon_button("edit-copy-symbolic", "Copy to clipboard")
        copy_button.connect("clicked", self._make_copy_handler(entry))

        delete_button = self._icon_button("user-trash-symbolic", "Delete entry")
        delete_button.connect("clicked", self._make_delete_handler(entry))

        row_box.pack_start(text_label, True, True, 0)
        row_box.pack_end(delete_button, False, False, 0)
        row_box.pack_end(copy_button, False, False, 0)
        row_box.pack_end(qr_button, False, False, 0)
        row_box.pack_end(pin_button, False, False, 0)

        row.add(row_box)
        return row

    def _icon_button(self, icon_name, tooltip):
        button = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        button.set_image(icon)
        button.set_tooltip_text(tooltip)
        return button

    def _make_copy_handler(self, entry):
        def handler(_button):
            pyperclip.copy(entry["content"])
            add_entry(entry["content"])
            self.refresh()

        return handler

    def _make_delete_handler(self, entry):
        def handler(_button):
            confirmed = self._confirm_delete(entry)
            if confirmed:
                delete_entry(entry["id"])
                self.refresh()

        return handler

    def _make_pin_handler(self, entry, is_pinned):
        def handler(_button):
            if is_pinned:
                unpin_entry(entry["id"])
                self.refresh()
                return

            oldest_conflict = pin_entry(entry["id"])
            if oldest_conflict is not None:
                if self._confirm_pin_swap(oldest_conflict):
                    unpin_entry(oldest_conflict["id"])
                    pin_entry(entry["id"])
            self.refresh()

        return handler

    def _make_qr_handler(self, entry):
        def handler(_button):
            if self.on_qr_clicked:
                self.on_qr_clicked(entry)
            else:
                print(f"QR requested for entry id={entry['id']}: {entry['content']!r}")

        return handler

    def on_delete_event(self, _widget, _event):
        self.hide()
        return True

    def show_window(self):
        self.refresh()
        self.show_all()
        self.present()


def open_qr_popup(entry):
    QrPopup(entry)


def _standalone_test():
    win = HistoryWindow(on_qr_clicked=open_qr_popup)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
