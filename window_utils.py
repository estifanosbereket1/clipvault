import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def safe_present(window):
    """
    Show/raise a window without tripping Wayland focus-stealing prevention.

    If we're inside a real user event (menu click, button press), GTK has a
    valid event timestamp and present_with_time() is a legitimate focus
    request. If there's no event (signal handler, idle callback), a plain
    present() would be denied by mutter and flag the window as
    'demands attention' -- which is what makes the dock icon shake.
    In that case we just map/raise the window without requesting focus.
    """
    window.show_all()
    timestamp = Gtk.get_current_event_time()
    if timestamp != 0:  # 0 == GDK_CURRENT_TIME == "no real event"
        window.present_with_time(timestamp)
    # else: no token available -- showing without a focus grab is the
    # polite option; the user's hands are on the keyboard anyway.
