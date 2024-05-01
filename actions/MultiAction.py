from data.plugins.AdvancedActionPlugin.internal.State import State
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class MultiAction(ActionBase):

    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
                         deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

    # DEFINE PER PLUGIN VARIABLES
    def on_ready(self):
        self.states = [State(1, self), State(2, self)]
        self.current_state_index = 0  # Used on Key Down Event

        self.load_sub_actions()

    # DEFINE UI
    def get_config_rows(self) -> "list[Adw.PreferencesRow]":
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Create Stack
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.NONE, transition_duration=0)
        self.stack_switcher = Gtk.StackSwitcher()
        self.stack_switcher.set_stack(self.stack)

        # Add Stack UI to main box
        self.main_box.append(self.stack_switcher)
        self.main_box.append(self.stack)

        # Add UI to Stack
        for state in self.states:
            if state.get_parent() is not None:
                state.get_parent().remove(state)
            self.stack.add_titled(state, f"state_{state.state_id}", f"State {state.state_id}")

        self.load_settings()

        return [self.main_box]

    def load_sub_actions(self):
        for state in self.states:
            state.load_sub_actions(self.get_settings())

    def load_settings(self):
        for state in self.states:
            state.load_settings(self.get_settings())