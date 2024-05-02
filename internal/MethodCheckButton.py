
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class MethodCheckButton(Gtk.CheckButton):
    def __init__(self, label, method):
        super().__init__(label=label)

        self.method: str | None = method

        self.connect("toggled", self.toggled)
        self.toggle_event: callable = None

    def toggled(self, checkbutton: Gtk.CheckButton):
        if self.toggle_event is None:
            return

        self.toggle_event(checkbutton.get_active(), self.method)