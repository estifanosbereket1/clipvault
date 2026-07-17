import gi
import pyperclip

from window_utils import safe_present

gi.require_version("Gtk", "3.0")
from datetime import datetime
from icon_loader import load_icon

from gi.repository import GLib, Gtk

from clipboard_wipe import schedule_wipe
from diff_display import DiffPopup
from qr_display import QrPopup
from settings_store import load_settings
from storage import (
    add_entry,
    delete_entry,
    get_pinned_entries,
    get_recent_unpinned,
    pin_entry,
    search_entries,
    toggle_self_destruct,
    unpin_entry,
)

from inspector_display import InspectorPopup


def format_relative_time(created_at_str: str) -> str:
    created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
    delta = datetime.utcnow() - created_at
    seconds = delta.total_seconds()

    if seconds < 60:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes}m ago"
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours}h ago"
    days = int(hours // 24)
    return f"{days}d ago"


STALE_THRESHOLD_MINUTES = 10

INSPECTABLE_TYPES = {"jwt", "json", "url"}


def is_stale(created_at_str: str) -> bool:
    created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
    delta = datetime.utcnow() - created_at
    return delta.total_seconds() > STALE_THRESHOLD_MINUTES * 60


def truncate(text: str, max_len: int = 60) -> str:
    """Shorten long clipboard text for display in the list."""
    text = text.replace("\n", " ")
    if len(text) > max_len:
        return text[:max_len].rstrip() + "..."
    return text


class HistoryWindow(Gtk.Window):
    def __init__(self, on_qr_clicked=None):
        super().__init__(title="ClipVault History")
        self.compare_mode = False
        self.selected_for_compare = []
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

        compare_toggle_btn = Gtk.Button(label="Compare Mode")
        compare_toggle_btn.connect("clicked", self.on_toggle_compare_mode)
        header.pack_end(compare_toggle_btn, False, False, 0)
        self.compare_toggle_btn = compare_toggle_btn

        self.compare_selected_btn = Gtk.Button(label="Compare Selected")
        self.compare_selected_btn.set_sensitive(False)
        self.compare_selected_btn.connect("clicked", self.on_compare_selected_clicked)
        self.compare_selected_btn.hide()
        outer_box.pack_start(self.compare_selected_btn, False, False, 0)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search clipboard history...")
        self.search_entry.connect("search-changed", self.on_search_changed)
        outer_box.pack_start(self.search_entry, False, False, 0)


        search_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        search_row.pack_start(self.search_entry, True, True, 0)

        self.regex_toggle = Gtk.ToggleButton(label=".*")
        self.regex_toggle.set_tooltip_text("Treat search as regex")
        self.regex_toggle.connect("toggled", lambda _btn: self.refresh())
        search_row.pack_start(self.regex_toggle, False, False, 0)

        self.type_filter_combo = Gtk.ComboBoxText()
        self.type_filter_combo.append("", "All types")
        for type_id, type_label in (
            ("json", "JSON"),
            ("jwt", "JWT"),
            ("url", "URL"),
            ("uuid", "UUID"),
            ("ip_address", "IP Address"),
            ("email", "Email"),
            ("code", "Code"),
            ("text", "Text"),
        ):
            self.type_filter_combo.append(type_id, type_label)
        self.type_filter_combo.set_active_id("")
        self.type_filter_combo.connect("changed", lambda _combo: self.refresh())
        search_row.pack_start(self.type_filter_combo, False, False, 0)

        outer_box.pack_start(search_row, False, False, 0)

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

        self.synced_expander = Gtk.Expander(label="Synced from other devices")
        outer_box.pack_start(self.synced_expander, False, False, 0)

        self.synced_list_box = Gtk.ListBox()
        self.synced_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.synced_expander.add(self.synced_list_box)

        self.refresh()

    def _format_secret_warning(self, secret_type):
        if not secret_type:
            return None
        return f"⚠ {secret_type}"

    def on_search_changed(self, _entry):
        self.refresh()

    def on_toggle_compare_mode(self, _button):
        self.compare_mode = not self.compare_mode
        self.selected_for_compare = []
        self.compare_toggle_btn.set_label(
            "Exit Compare Mode" if self.compare_mode else "Compare Mode"
        )
        self.compare_selected_btn.set_visible(self.compare_mode)
        self.compare_selected_btn.set_sensitive(False)
        self.refresh()

    def on_compare_selected_clicked(self, _button):
        if len(self.selected_for_compare) != 2:
            return
        ordered = sorted(self.selected_for_compare, key=lambda e: e["created_at"])
        DiffPopup(ordered[0]["content"], ordered[1]["content"])

    def _make_compare_checkbox_handler(self, entry):
        def handler(checkbox):
            if checkbox.get_active():
                self.selected_for_compare.append(entry)
            else:
                self.selected_for_compare = [
                    e for e in self.selected_for_compare if e["id"] != entry["id"]
                ]
            self.compare_selected_btn.set_sensitive(len(self.selected_for_compare) == 2)
            self.refresh()
        return handler

    def _get_search_query(self) -> str:
        return self.search_entry.get_text().strip()

    def refresh(self):
        """Reload entries from storage and rebuild both sections."""
        for child in self.pinned_list_box.get_children():
            self.pinned_list_box.remove(child)
        for child in self.list_box.get_children():
            self.list_box.remove(child)



        query = self._get_search_query()

        # if query:
        #     matched_entries = search_entries(query, limit=100)
        #     local_entries = [e for e in matched_entries if e["origin"] == "local"]
        #     synced_entries = [e for e in matched_entries if e["origin"] != "local"]
        # else:
        #     recent_entries = get_recent_unpinned(limit=load_settings()["history_limit"])
        #     # local_entries = [e for e in recent_entries if e["origin"] == "local"]
        #     # synced_entries = [e for e in recent_entries if e["origin"] != "local"]
        #     local_entries = [e for e in recent_entries if e["origin"] in ("local", "phone")]
        #     synced_entries = [e for e in recent_entries if e["origin"] not in ("local", "phone")]

        query = self._get_search_query()
        use_regex = self.regex_toggle.get_active()
        type_filter = self.type_filter_combo.get_active_id() or None

        if query:
            matched_entries = search_entries(query, limit=100, use_regex=use_regex, content_type_filter=type_filter)
            local_entries = [e for e in matched_entries if e["origin"] in ("local", "phone")]
            synced_entries = [e for e in matched_entries if e["origin"] not in ("local", "phone")]
        else:
            recent_entries = get_recent_unpinned(limit=load_settings()["history_limit"])
            local_entries = [e for e in recent_entries if e["origin"] in ("local", "phone")]
            synced_entries = [e for e in recent_entries if e["origin"] not in ("local", "phone")]

        if not query:
            pinned_entries = get_pinned_entries()
            if pinned_entries:
                self.pinned_label.show()
                for entry in pinned_entries:
                    row = self._build_row(entry, is_pinned=True, previous_entry=None)
                    self.pinned_list_box.add(row)
            else:
                self.pinned_label.hide()
        else:
            self.pinned_label.hide()
        if not local_entries:
            empty_label = Gtk.Label(
                label="No matching entries." if query else "No clipboard history yet."
            )
            empty_label.set_margin_top(20)
            self.list_box.add(empty_label)
        else:
            for index, entry in enumerate(local_entries):
                previous_entry = local_entries[index + 1] if index + 1 < len(local_entries) else None
                row = self._build_row(entry, is_pinned=False, previous_entry=previous_entry)
                self.list_box.add(row)

        for child in self.synced_list_box.get_children():
            self.synced_list_box.remove(child)

        if synced_entries:
            self.synced_expander.set_label(f"Synced from other devices ({len(synced_entries)})")
            self.synced_expander.show()
            for index, entry in enumerate(synced_entries):
                previous_entry = synced_entries[index + 1] if index + 1 < len(synced_entries) else None
                row = self._build_row(entry, is_pinned=False, previous_entry=previous_entry)
                self.synced_list_box.add(row)
        else:
            self.synced_expander.hide()

        self.synced_list_box.show_all()



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

    def _build_row(self, entry, is_pinned: bool, previous_entry=None) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row_box.set_margin_top(4)
        row_box.set_margin_bottom(4)
        row_box.set_margin_start(6)
        row_box.set_margin_end(6)

        # --- badge ---
        # badge_text = self._format_badge(entry["content_type"])
        # if entry["origin"] != "local":
        #     peer_label_text = entry["origin"].split(".")[0]  # strip the .local. suffix etc, just show hostname
        #     origin_label = Gtk.Label(label=f"↴ {peer_label_text}")
        #     origin_label.get_style_context().add_class("dim-label")
        #     row_box.pack_start(origin_label, False, False, 0)

        badge_text = self._format_badge(entry["content_type"])
        if badge_text:
            badge_label = Gtk.Label(label=badge_text)
            badge_label.get_style_context().add_class("dim-label")
            row_box.pack_start(badge_label, False, False, 0)

        secret_type = entry["contains_secret"] if "contains_secret" in entry.keys() else None
        secret_warning = self._format_secret_warning(secret_type)
        if secret_warning:
            secret_label = Gtk.Label(label=secret_warning)
            secret_label.get_style_context().add_class("secret-warning-label")
            secret_label.set_tooltip_text(
                f"This looks like a {secret_type}. Consider marking it as self-destruct."
            )
            row_box.pack_start(secret_label, False, False, 0)

        if entry["origin"] == "phone":
            origin_label = Gtk.Label(label="📱 from phone")
            origin_label.get_style_context().add_class("dim-label")
            row_box.pack_start(origin_label, False, False, 0)
        elif entry["origin"] != "local":
            peer_label_text = entry["origin"].split(".")[0]
            origin_label = Gtk.Label(label=f"↴ {peer_label_text}")
            origin_label.get_style_context().add_class("dim-label")
            row_box.pack_start(origin_label, False, False, 0)

        # --- time label + stale icon, grouped in their own small box ---
        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        stale = is_stale(entry["created_at"])
        if stale:
            stale_icon = load_icon("alarm-clock", size=14)
            stale_icon.set_tooltip_text("This entry may be stale")
            time_box.pack_start(stale_icon, False, False, 0)
        time_label = Gtk.Label(label=format_relative_time(entry["created_at"]))
        time_label.get_style_context().add_class("dim-label")
        time_box.pack_start(time_label, False, False, 0)
        row_box.pack_start(time_box, False, False, 0)

        text_label = Gtk.Label(label=truncate(entry["content"]))
        text_label.set_xalign(0)
        text_label.set_hexpand(True)
        text_label.set_ellipsize(3)
        if stale:
            text_label.get_style_context().add_class("dim-label")

        row_box.pack_start(text_label, True, True, 0)

        if self.compare_mode:
            checkbox = Gtk.CheckButton()
            is_selected = any(e["id"] == entry["id"] for e in self.selected_for_compare)
            checkbox.set_active(is_selected)
            if len(self.selected_for_compare) >= 2 and not is_selected:
                checkbox.set_sensitive(False)
            checkbox.connect("toggled", self._make_compare_checkbox_handler(entry))
            row_box.pack_end(checkbox, False, False, 0)
        else:
            if previous_entry is not None:
                diff_button = self._icon_button("git-compare", "Compare with previous entry")
                diff_button.connect(
                    "clicked", self._make_diff_handler(entry, previous_entry)
                )
                row_box.pack_end(diff_button, False, False, 0)
            if entry["content_type"] in INSPECTABLE_TYPES:
                inspect_button = self._icon_button("search", "Inspect")
                inspect_button.connect("clicked", self._make_inspect_handler(entry))
                row_box.pack_end(inspect_button, False, False, 0)

            pin_icon = "star-filled" if is_pinned else "star"
            pin_tooltip = "Unpin" if is_pinned else "Pin (max 5)"
            pin_button = self._icon_button(pin_icon, pin_tooltip)
            pin_button.connect("clicked", self._make_pin_handler(entry, is_pinned))

            burn_icon = "flame-active" if entry["self_destruct"] else "flame"
            burn_tooltip = (
                "Self-destruct: ON (copy will auto-delete + wipe clipboard)"
                if entry["self_destruct"]
                else "Mark as self-destruct"
            )
            burn_button = self._icon_button(burn_icon, burn_tooltip)
            burn_button.connect("clicked", self._make_burn_toggle_handler(entry))

            qr_button = self._icon_button("qr-code", "Show QR code")
            qr_button.connect("clicked", self._make_qr_handler(entry))

            copy_button = self._icon_button("copy", "Copy to clipboard")
            copy_button.connect("clicked", self._make_copy_handler(entry))

            delete_button = self._icon_button("trash-2", "Delete entry")
            delete_button.connect("clicked", self._make_delete_handler(entry))

            row_box.pack_end(burn_button, False, False, 0)
            row_box.pack_end(delete_button, False, False, 0)
            row_box.pack_end(copy_button, False, False, 0)
            row_box.pack_end(qr_button, False, False, 0)
            row_box.pack_end(pin_button, False, False, 0)

        row.add(row_box)
        return row




    def _icon_button(self, icon_name, tooltip):
        button = Gtk.Button()
        button.set_image(load_icon(icon_name))
        button.set_tooltip_text(tooltip)
        return button

    def _make_inspect_handler(self, entry):
        def handler(_button):
            InspectorPopup(entry["content"], entry["content_type"])
        return handler

    def _make_diff_handler(self, entry, previous_entry):
        def handler(_button):
            DiffPopup(previous_entry["content"], entry["content"])

        return handler

    def _make_burn_toggle_handler(self, entry):
        def handler(_button):
            toggle_self_destruct(entry["id"])
            self.refresh()

        return handler

    def _make_copy_handler(self, entry):
        def handler(_button):
            pyperclip.copy(entry["content"])

            if entry["self_destruct"]:
                delete_entry(entry["id"])
                schedule_wipe(entry["content"])
            else:
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

    # def show_window(self):
    #     self.refresh()
    #     self.show_all()
    #     self.present()
    def show_window(self):
        self.refresh()
        safe_present(self)


def open_qr_popup(entry):
    QrPopup(entry)


def _standalone_test():
    win = HistoryWindow(on_qr_clicked=open_qr_popup)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
