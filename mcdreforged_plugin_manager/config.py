import os

from mcdreforged.api.all import *
from ruamel.yaml import YAML, CommentedMap

from mcdreforged_plugin_manager.constants import psi


class Configure(Serializable):
    CONFIG_PATH = os.path.join(psi.get_data_folder(), 'config.yml')
    DEFAULT_CONFIG = psi.open_bundled_file('resources/default_config.yml')

    permission: int = PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL
    source: str = 'https://raw.githubusercontent.com/MCDReforged/PluginCatalogue/meta'
    timeout: int = 15
    cache_interval: int = 30
    check_update: bool = True

    @property
    def get_source(self) -> str:
        return self.source.rstrip('/')

    @classmethod
    def load(cls) -> 'Configure':
        if not os.path.isfile(cls.CONFIG_PATH):
            cls.__save_default()
            default = cls.get_default()
            return default
        with open(cls.CONFIG_PATH, 'r', encoding='UTF-8') as f:
            data = YAML().load(f)
        return cls.deserialize(data)

    @classmethod
    def __save_default(cls):
        if not os.path.isdir(os.path.dirname(cls.CONFIG_PATH)):
            os.makedirs(os.path.dirname(cls.CONFIG_PATH))
        with open(cls.CONFIG_PATH, 'w', encoding='utf8') as file:
            data: CommentedMap = YAML().load(cls.DEFAULT_CONFIG)
            YAML().dump(data, file)


config = Configure.load()
