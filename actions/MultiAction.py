from GtkHelper.GtkHelper import ComboRow
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

    '''
    DEFINE WHEN TO SWITCH STATE
    BEFORE STATE GETS SWITCHED EXECUTE ACTION METHOD IN STATE

    DEFINE METHOD(S) THAT GETS EXECUTED IN STATE WHEN STATE SWITCHES
    '''

    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
                         deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

    #
    # OVERRIDEN
    #

    def on_ready(self):
        self.triggers = [
            ("On Key Down", "OKD"),
            ("On Key Up", "OKU"),
            ("On Tick", "OT")
        ]

        self.states = [State(1, self), State(2, self)]
        self.current_state_index = 0  # Used on Key Down Event

        self.load_sub_actions()

    def get_custom_config_area(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Create Switch Model
        self.state_swtich_model = Gtk.ListStore.new([str, str])

        # Create Switch Combo Row
        self.state_swtich_row = ComboRow(title="Switch Behaviour", model=self.state_swtich_model)

        # Create State Switch Renderer
        self.state_switch_renderer = Gtk.CellRendererText()

        # Assign Cell Renderer
        self.state_swtich_row.combo_box.pack_start(self.state_switch_renderer, True)
        self.state_swtich_row.combo_box.add_attribute(self.state_switch_renderer, "text", 0)

        # Add State Switch to main Box
        self.main_box.append(self.state_swtich_row)

        # Create Stack
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.NONE, transition_duration=0)
        self.stack_switcher = Gtk.StackSwitcher()
        self.stack_switcher.set_stack(self.stack)

        # Add Stack UI to main box
        self.main_box.append(self.stack_switcher)
        self.main_box.append(self.stack)

        # Connect Events
        self.state_swtich_row.combo_box.connect("changed", self.state_switch_changed)

        # Add UI to Stack
        for state in self.states:
            if state.get_parent() is not None:
                state.get_parent().remove(state)
            self.stack.add_titled(state, f"state_{state.state_id}", f"State {state.state_id}")

        # Load Models
        self.load_switch_model()

        # Load Settings
        self.load_settings()

        return self.main_box

    #
    # SETTINGS
    #

    def load_sub_actions(self):
        for state in self.states:
            state.load_sub_actions(self.get_settings())

        self.states[self.current_state_index].enable_visual_methods()

    def load_settings(self):
        settings = self.get_settings()
        behaviour_code = settings.get("switch-behaviour")

        for state in self.states:
            state.load_settings(settings)

        for i, code in enumerate(self.state_swtich_model):
            if code[1] == behaviour_code:
                self.state_swtich_row.combo_box.set_active(i)
                break

        if behaviour_code == None:
            self.state_swtich_row.combo_box.set_active(0)

    #
    # MODELS
    #

    def load_switch_model(self):
        for trigger in self.triggers:
            self.state_swtich_model.append(trigger)

    #
    # EVENTS
    #

    def state_switch_changed(self, combo_box, *args):
        settings = self.get_settings()

        behaviour_code = self.state_swtich_model[combo_box.get_active()][1]

        settings["switch-behaviour"] = behaviour_code
        self.set_settings(settings)

    #
    # MISC
    #

    def execute_triggers(self, callback_key: str):
        settings = self.get_settings()
        state = self.states[self.current_state_index]

        triggers = settings.get(state.SETTING_IDENTIFIER, {}).get("method-triggers") or []

        for trigger in triggers:
            if trigger not in state.overridden_methods:
                continue
            if state.action is None or state.action.action is None:
                continue

            if trigger == "OKD" and trigger == callback_key:
                state.action.action.on_key_down()
            elif trigger == "OKU" and trigger == callback_key:
                state.action.action.on_key_up()
            elif trigger == "OT" and trigger == callback_key:
                state.action.action.on_tick()

    def change_state(self, behaviour_key: str):
        settings = self.get_settings()
        settings_behaviour = settings.get("switch-behaviour") or "OKD"

        if behaviour_key == settings_behaviour:
            self.states[self.current_state_index].disable_visual_methods()

            self.current_state_index = 1 if self.current_state_index == 0 else 0

            self.states[self.current_state_index].enable_visual_methods()

    #
    # KEY ACTIONS
    #

    def on_key_down(self):
        self.execute_triggers("OKD")
        self.change_state("OKD")

    def on_key_up(self):
        self.execute_triggers("OKU")
        self.change_state("OKU")

    def on_tick(self):
        self.execute_triggers("OT")
        self.change_state("OT")