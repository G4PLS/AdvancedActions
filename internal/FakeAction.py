import globals as gl
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.PluginBase import PluginBase

class FakePluginBase(PluginBase):
    def __init__(self):
        super().__init__()

class FakeAction:
    def __init__(self, action_id: str, action_name: str, parent_plugin: PluginBase, parent_action: ActionBase, deck_controller: DeckController, page: Page, coords: (int, int), state_id: int):
        self.global_action_holder: ActionHolder = gl.plugin_manager.action_index.get(action_id)

        if self.global_action_holder is None:
            return

        self.parent_plugin = parent_plugin
        self.parent_action = parent_action

        self.state_id = state_id

        plugin_id = gl.plugin_manager.get_plugin_id_from_action_id(action_id)
        self.plugin_base = gl.plugin_manager.get_plugin_by_id(plugin_id)

        self.action_id = action_id
        self.action_name = action_name

        self.action_holder = ActionHolder(
            plugin_base=self.plugin_base,
            action_base=self.global_action_holder.action_base,
            action_id=self.action_id,
            action_name=self.action_name
        )

        final_coords = 'x'.join(str(element) for element in coords)
        self.action = self.action_holder.init_and_get_action(deck_controller=deck_controller, page=page, coords=final_coords)

        self.action.set_settings = self.set_settings
        self.action.get_settings = self.get_settings

    def set_settings(self, settings: dict) -> None:
        base_settings = self.parent_action.get_settings()

        merged_settings: dict = base_settings.get(f"State-{self.state_id}")

        if merged_settings is None:
            return
        merged_settings.update(settings)

        base_settings[f"State-{self.state_id}"] = merged_settings

        self.parent_action.set_settings(base_settings)

    def get_settings(self):
        settings = self.parent_action.get_settings()

        state_settings = settings.get(f"State-{self.state_id}")

        if state_settings:
            return state_settings
        return {}

        #print(settings)

        #settings.get(f"State-{self.state_id}")

        #print(settings)