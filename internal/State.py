from GtkHelper.GtkHelper import ComboRow
from data.plugins.AdvancedActionPlugin.internal.FakeAction import FakeAction

import gi

from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.PluginBase import PluginBase


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

        self.build()

    #
    # CREATE UI
    #

    def build(self):
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

        # Create Plugin UI Field
        self.plugin_ui = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append(self.plugin_ui)

        # Connect Events
        self.plugin_row.combo_box.connect("changed", self.plugin_changed)
        self.action_row.combo_box.connect("changed", self.action_changed)

        # Load Plugin Model
        #self.load_plugin_model()

    def load_action_ui(self):
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

        self.load_action_ui()

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
        self.load_action_ui()

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

        self.load_action_ui()

        self.plugin_row.combo_box.connect("changed", self.plugin_changed)
        self.action_row.combo_box.connect("changed", self.action_changed)

    def set_state_settings(self, plugin_id, action_id):
        settings = self.base_action.get_settings()
        state_settings = settings.get(self.SETTING_IDENTIFIER) or {}

        state_plugin_id = state_settings.get("plugin-id")
        state_action_id = state_settings.get("action-id")

        if state_action_id != action_id:
            state_settings = {"plugin-id": plugin_id, "action-id": action_id}
        if state_plugin_id != plugin_id:
            state_settings = {"plugin-id": plugin_id, "action-id": action_id}

        print(self.SETTING_IDENTIFIER)
        print(state_settings)
        print("#####")

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

        self.load_action_ui()