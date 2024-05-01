from src.backend.PluginManager.EventHolder import EventHolder
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder
import globals as gl

# Import actions
from .actions.MultiAction import MultiAction

class AdvancedActions(PluginBase):
    def __init__(self):
        super().__init__()
        self.init_vars()

        ## Register actions
        self.multi_action_holder = ActionHolder(
            plugin_base=self,
            action_base=MultiAction,
            action_id=f"{self.get_manifest().get('id')}::Multi",
            action_name="Multi Action"
        )
        self.add_action_holder(self.multi_action_holder)

        self.register()

    def init_vars(self):
        self.lm = self.locale_manager