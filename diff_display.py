import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from diff_utils import format_summary, get_diff


class DiffPopup(Gtk.Window):
    def __init__(self, old_content: str, new_content: str):
        super().__init__(title="Compare with previous entry")
        self.set_default_size(500, 400)
        self.set_position(Gtk.WindowPosition.CENTER)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.set_border_width(12)
        self.add(outer)

        result = get_diff(old_content, new_content)

        summary_label = Gtk.Label(label=format_summary(result["summary"]))
        summary_label.set_xalign(0)
        outer.pack_start(summary_label, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        outer.pack_start(scrolled, True, True, 0)

        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_monospace(True)
        buffer = text_view.get_buffer()

        buffer.create_tag("add", foreground="#4caf50")
        buffer.create_tag("remove", foreground="#f44336")
        buffer.create_tag("modified", foreground="#ff9800")
        buffer.create_tag("same", foreground="#9e9e9e")

        for line_type, content in result["lines"]:
            marker = {"add": "+ ", "remove": "- ", "same": "  ", "modified": "~ "}[
                line_type
            ]
            end_iter = buffer.get_end_iter()
            buffer.insert_with_tags_by_name(
                end_iter, marker + content + "\n", line_type
            )

        scrolled.add(text_view)
        self.show_all()


def _standalone_test():
    old = "line one\nline two\nline three"
    new = "line one\nline TWO changed\nline three\nline four added"
    win = DiffPopup(old, new)
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    _standalone_test()
