from copy import deepcopy

from GtkHelper.GtkHelper import ComboRow
from data.plugins.AdvancedActionPlugin.internal.FakeAction import FakeAction

from loguru import logger as log
import gi

from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.PluginBase import PluginBase

from ..internal.MethodCheckButton import MethodCheckButton

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

import globals as gl


class State(Gtk.Box):
    def __init__(self, state_id: int, base_action: ActionBase):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.action: FakeAction | None = None
        self.state_id: int = state_id
        self.base_action = ActionBase = base_action
        self.available_actions: list[ActionHolder] = []
        self.SETTING_IDENTIFIER = f"State-{self.state_id}"

        self.overridden_methods: list[str] = []  # Actual Methods that are overridden by the selected Action
        self.method_translations: dict[str, str] = {
            "OKD": "On Key Down",
            "OKU": "On Key Up",
            "OT": "On Tick"
        }

        self.build()

    #
    # CREATE UI
    #

    def build(self):
        self.build_selection()

        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        self.build_settings()

        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Create Plugin UI Field
        self.plugin_ui = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append(self.plugin_ui)

        # Connect Events
        self.plugin_row.combo_box.connect("changed", self.plugin_changed)
        self.action_row.combo_box.connect("changed", self.action_changed)

    def build_selection(self):
        # Create Models
        self.plugin_model = Gtk.ListStore.new([str])
        self.action_model = Gtk.ListStore.new([str])

        # Create Combo Rows
        self.plugin_row = ComboRow(title="Plugin", model=self.plugin_model)
        self.action_row = ComboRow(title="Action", model=self.action_model)

        # Create Cell Renderer
        self.plugin_renderer = Gtk.CellRendererText()
        self.action_renderer = Gtk.CellRendererText()

        # Assign Cell Renderers
        self.plugin_row.combo_box.pack_start(self.plugin_renderer, True)
        self.plugin_row.combo_box.add_attribute(self.plugin_renderer, "text", 0)

        self.action_row.combo_box.pack_start(self.action_renderer, True)
        self.action_row.combo_box.add_attribute(self.action_renderer, "text", 0)

        # Add UI to Box
        self.append(self.plugin_row)
        self.append(self.action_row)

    def build_settings(self):
        # Create Settings Section
        self.settings_group = Adw.PreferencesGroup(title="State Settings")

        self.trigger_row = Adw.PreferencesRow(title="Triggers")

        self.trigger_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_end=10, margin_start=10)

        self.trigger_row.set_child(self.trigger_box)

        self.trigger_label = Gtk.Label(label="Triggers", hexpand=True, xalign=0)
        self.trigger_box.append(self.trigger_label)

        self.trigger_grid = Gtk.Grid()
        self.trigger_box.append(self.trigger_grid)

        self.build_trigger_grid()

        self.settings_group.add(self.trigger_row)

        self.append(self.settings_group)

    def build_trigger_grid(self):
        self.trigger_box.remove(self.trigger_grid)

        self.trigger_grid = Gtk.Grid()

        self.trigger_grid.set_column_spacing(5)
        self.trigger_grid.set_row_spacing(5)

        for i, overridden_method in enumerate(self.overridden_methods):
            check_box = MethodCheckButton(label=self.method_translations.get(overridden_method),
                                          method=overridden_method)
            check_box.toggle_event = self.checkbutton_toggled
            self.trigger_grid.attach(check_box, 0, i, 1, 1)

        self.trigger_box.append(self.trigger_grid)

    def build_action_ui(self):
        self.remove(self.plugin_ui)

        if self.action is None:
            return

        self.plugin_ui = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        custom_area = self.action.action.get_custom_config_area()
        elements = self.action.action.get_config_rows() or []
        if custom_area:
            elements.append(custom_area)

        for element in elements:
            self.plugin_ui.append(element)

        self.append(self.plugin_ui)

    #
    # LOAD MODELS
    #

    def load_plugin_model(self):
        plugins = gl.plugin_manager.get_plugins().items()

        self.plugin_model.clear()
        self.action_model.clear()

        for plugin in plugins:
            self.plugin_model.append([plugin[0]])

    def load_action_model(self):
        self.action_model.clear()

        for action_holder in self.available_actions:
            self.action_model.append([action_holder])

    #
    # EVENTS
    #

    def plugin_changed(self, combo_box, *args):
        plugin_id: str = self.plugin_model[combo_box.get_active()][0]

        self.action = None

        # Load available actions
        plugin = gl.plugin_manager.get_plugin_by_id(plugin_id)
        self.available_actions = plugin.action_holders

        self.action_row.combo_box.disconnect_by_func(self.action_changed)
        self.load_action_model()
        self.action_row.combo_box.connect("changed", self.action_changed)

        self.build_action_ui()

        self.get_action_methods()
        self.build_trigger_grid()

        # Set Settings
        self.set_state_settings(plugin_id, None)

    def action_changed(self, combo_box, *args):
        settings = self.base_action.get_settings()
        plugin_id = settings.get(self.SETTING_IDENTIFIER, {}).get("plugin-id")

        action_id = self.action_model[combo_box.get_active()][0]

        if action_id:
            self.set_action(
                action_id=action_id,
                action_name=f"{self.base_action.action_name}::State_{self.state_id}::Action",
                parent_plugin=self.base_action.plugin_base,
                deck_controller=self.base_action.deck_controller,
                page=self.base_action.page,
                coords=self.base_action.coords,
                state_id=self.state_id,
            )

        self.set_state_settings(plugin_id, action_id)
        self.build_action_ui()

    def checkbutton_toggled(self, state, method):
        settings = self.base_action.get_settings()

        state_settings = settings.get(self.SETTING_IDENTIFIER)

        triggers = state_settings.get("method-triggers") or []

        if method in triggers:
            for trigger in triggers:
                if trigger == method and state is True and method not in triggers:
                    triggers.append(method)
                    break
                if trigger == method and state is False and method in triggers:
                    triggers.remove(method)
                    break
        else:
            triggers.append(method)

        state_settings["method-triggers"] = triggers

        settings[self.SETTING_IDENTIFIER] = state_settings

        self.base_action.set_settings(settings)

    #
    # SETTINGS
    #

    def load_sub_actions(self, settings):
        state_settings = settings.get(self.SETTING_IDENTIFIER) or {}

        plugin_id = state_settings.get("plugin-id")
        action_id = state_settings.get("action-id")

        if plugin_id is None or action_id is None:
            return

        self.set_action(
            action_id=action_id,
            action_name=f"{self.base_action.action_name}::State_{self.state_id}::Action",
            parent_plugin=self.base_action.plugin_base,
            deck_controller=self.base_action.deck_controller,
            page=self.base_action.page,
            coords=self.base_action.coords,
            state_id=self.state_id,
        )

    def load_settings(self, settings):
        state_settings = settings.get(self.SETTING_IDENTIFIER) or {}

        plugin_id = state_settings.get("plugin-id")
        action_id = state_settings.get("action-id")

        # Disconnect events to not trigger change events
        self.plugin_row.combo_box.disconnect_by_func(self.plugin_changed)
        self.action_row.combo_box.disconnect_by_func(self.action_changed)

        self.load_plugin_model()

        plugin = gl.plugin_manager.get_plugin_by_id(plugin_id)

        if plugin:
            self.available_actions = plugin.action_holders

        self.load_action_model()

        for i, plugin in enumerate(self.plugin_model):
            if plugin[0] == plugin_id:
                self.plugin_row.combo_box.set_active(i)
                break

        if plugin_id:
            for i, action in enumerate(self.action_model):
                if action[0] == action_id:
                    self.action_row.combo_box.set_active(i)
                    break

        if plugin_id is None:
            self.plugin_row.combo_box.set_active(-1)
        if action_id is None or plugin_id is None:
            self.action_row.combo_box.set_active(-1)

        self.build_action_ui()

        # Reconnect events
        self.plugin_row.combo_box.connect("changed", self.plugin_changed)
        self.action_row.combo_box.connect("changed", self.action_changed)

    def set_state_settings(self, plugin_id, action_id):
        # Get Settings for correct State
        settings = self.base_action.get_settings()
        state_settings = settings.get(self.SETTING_IDENTIFIER) or {}

        # Get IDs
        state_plugin_id = state_settings.get("plugin-id")
        state_action_id = state_settings.get("action-id")

        # Update IDs when they dont match anymore
        if state_action_id != action_id:
            state_settings = {"plugin-id": plugin_id, "action-id": action_id}
        if state_plugin_id != plugin_id:
            state_settings = {"plugin-id": plugin_id, "action-id": action_id}

        # Set Settings
        settings[self.SETTING_IDENTIFIER] = state_settings
        self.base_action.set_settings(settings)

    #
    # ACTION
    #

    def set_action(self, action_id: str, action_name: str, parent_plugin: PluginBase, deck_controller: DeckController,
                   page: Page, coords: (int, int), state_id: int):
        self.action = FakeAction(
            action_id=action_id,
            action_name=action_name,
            parent_plugin=parent_plugin,
            deck_controller=deck_controller,
            page=page,
            coords=coords,
            state_id=state_id,
            parent_action=self.base_action
        )

        self.action.action.on_ready()

        self.build_action_ui()
        self.get_action_methods()
        self.build_trigger_grid()

    def get_action_methods(self):
        self.overridden_methods = []

        if self.action is None or self.action.action is None:
            return

        action: ActionBase = self.action.action

        if not issubclass(type(action), ActionBase):
            return

        # Check Method Overloads
        if type(action).on_key_down != ActionBase.on_key_down:
            self.overridden_methods.append("OKD")
        if type(action).on_key_up != ActionBase.on_key_up:
            self.overridden_methods.append("OKU")
        if type(action).on_tick != ActionBase.on_tick:
            self.overridden_methods.append("OT")

    def enable_visual_methods(self):
        if self.action is None and self.action.action is None:
            return
        action = self.action.action

        action.set_label = self.base_action.set_label
        action.set_media = self.base_action.set_media

    def disable_visual_methods(self):
        if self.action is None and self.action.action is None:
            return
        action = self.action.action

        action.set_label = self.set_label
        action.set_media = self.set_media

    def set_media(self, image=None, media_path=None, size: float = None, valign: float = None, halign: float = None,
                  fps: int = 30, loop: bool = True, update: bool = True):
        return

    def set_label(self, text: str, position: str = "bottom", color: list[int] = None,
    font_family: str = None, font_size = None, update: bool = True):
        return