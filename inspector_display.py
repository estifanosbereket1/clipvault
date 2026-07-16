import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import pyperclip

from inspector import inspect_jwt, inspect_json, inspect_url


class InspectorPopup(Gtk.Window):
    def __init__(self, content: str, content_type: str):
        super().__init__(title="Inspect")
        self.set_default_size(480, 420)
        self.set_position(Gtk.WindowPosition.CENTER)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.add(scrolled)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        outer.set_border_width(16)
        scrolled.add(outer)

        if content_type == "jwt":
            self._build_jwt_view(outer, content)
        elif content_type == "json":
            self._build_json_view(outer, content)
        elif content_type == "url":
            self._build_url_view(outer, content)
        else:
            outer.pack_start(Gtk.Label(label="No inspector available for this type."), False, False, 0)

        self.show_all()

    def _copy_button(self, text: str) -> Gtk.Button:
        btn = Gtk.Button(label="Copy")
        btn.connect("clicked", lambda _b: pyperclip.copy(text))
        return btn

    def _build_jwt_view(self, outer, content):
        result = inspect_jwt(content)

        if result["error"]:
            outer.pack_start(Gtk.Label(label=f"Couldn't decode: {result['error']}"), False, False, 0)
            return

        if result["expiry_info"]:
            expiry_label = Gtk.Label(label=result["expiry_info"])
            expiry_label.get_style_context().add_class("dim-label")
            outer.pack_start(expiry_label, False, False, 0)

        import json as json_module

        for section_name, data in (("Header", result["header"]), ("Payload", result["payload"])):
            title = Gtk.Label()
            title.set_markup(f"<b>{section_name}</b>")
            title.set_xalign(0)
            outer.pack_start(title, False, False, 6)

            pretty = json_module.dumps(data, indent=2)
            self._add_text_view(outer, pretty)

    def _build_json_view(self, outer, content):
        result = inspect_json(content)

        if result["error"]:
            outer.pack_start(Gtk.Label(label=f"Couldn't parse: {result['error']}"), False, False, 0)
            return

        self._add_text_view(outer, result["pretty"])

        copy_btn = self._copy_button(result["pretty"])
        copy_btn.set_label("Copy formatted JSON")
        outer.pack_start(copy_btn, False, False, 6)

    def _build_url_view(self, outer, content):
        result = inspect_url(content)

        if result["error"]:
            outer.pack_start(Gtk.Label(label=f"Couldn't parse: {result['error']}"), False, False, 0)
            return

        rows = [
            ("Scheme", result["scheme"]),
            ("Hostname", result["hostname"]),
            ("Path", result["path"]),
        ]
        for label_text, value in rows:
            self._add_labeled_row(outer, label_text, value)

        if result["query_params"]:
            title = Gtk.Label()
            title.set_markup("<b>Query parameters</b>")
            title.set_xalign(0)
            outer.pack_start(title, False, False, 6)
            for key, value in result["query_params"].items():
                self._add_labeled_row(outer, key, str(value))

        open_btn = Gtk.Button(label="Open in browser")
        open_btn.connect("clicked", lambda _b: Gtk.show_uri_on_window(None, content, 0))
        outer.pack_start(open_btn, False, False, 10)

    def _add_labeled_row(self, outer, label_text, value):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        label = Gtk.Label(label=f"{label_text}:")
        label.get_style_context().add_class("dim-label")
        label.set_xalign(0)
        value_label = Gtk.Label(label=value)
        value_label.set_xalign(0)
        value_label.set_selectable(True)
        value_label.set_line_wrap(True)
        row.pack_start(label, False, False, 0)
        row.pack_start(value_label, True, True, 0)
        row.pack_end(self._copy_button(value), False, False, 0)
        outer.pack_start(row, False, False, 2)

    def _add_text_view(self, outer, text):
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_monospace(True)
        text_view.get_buffer().set_text(text)
        text_view.set_size_request(-1, 120)
        outer.pack_start(text_view, False, False, 0)


def _standalone_test():
    win = InspectorPopup(
        content='{"name": "test", "value": 42}',
        content_type="json",
    )
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
