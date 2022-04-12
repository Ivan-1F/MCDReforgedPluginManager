import os

from mcdreforged.api.all import *
from ruamel.yaml import YAML

from mcdreforged_plugin_manager.constants import psi


class Configure(Serializable):
    CONFIG_PATH = os.path.join(psi.get_data_folder(), 'config.yml')

    permission: int = PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL
    source: str = 'https://raw.githubusercontent.com/MCDReforged/PluginCatalogue/meta/plugins.json'

    @classmethod
    def load(cls) -> 'Configure':
        if not os.path.isfile(cls.CONFIG_PATH):
            default = cls.get_default()
            default.save()
            return default
        with open(cls.CONFIG_PATH, 'r', encoding='UTF-8') as f:
            data = YAML().load(f)
        return cls.deserialize(data)

    def save(self):
        if not os.path.isdir(os.path.dirname(self.CONFIG_PATH)):
            os.makedirs(os.path.dirname(self.CONFIG_PATH))
        with open(self.CONFIG_PATH, 'w+', encoding='UTF-8') as f:
            YAML().dump(self.serialize(), f)


config: Configure = Configure.load()
