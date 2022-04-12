import json
import os
from typing import List, Dict

import requests
from mcdreforged.api.all import *

from mcdreforged_plugin_manager.config import config
from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.util.translation import tr


class MetaInfo(Serializable):
    id: str
    name: str
    version: str
    repository: str
    labels: List[str]
    authors: List[str]
    dependencies: Dict[str, str]
    requirements: List[str]
    description: Dict[str, str]

    @property
    def translated_description(self) -> str:
        language = psi.get_mcdr_language()
        text = self.description.get(language)
        if text is None:
            text = list(self.description.values())[0]
        return text


class PluginMetaInfoStorage(Serializable):
    plugin_amount: int = 0
    plugins: List[MetaInfo]

    def update(self, plugin_amount: int, plugins: List[MetaInfo]):
        # not using Serializable#update_from since it will update this cache method
        self.plugin_amount = plugin_amount
        self.plugins = plugins


class Cache(PluginMetaInfoStorage):
    CACHE_PATH = os.path.join(psi.get_data_folder(), 'cache.json')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache()

    @new_thread('mpm-cache')
    def cache(self):
        try:
            psi.logger.info(tr('cache.cache'))
            data = requests.get(config.source).json()
            self.update(data['plugin_amount'], list(data['plugins'].values()))
            self.save()
        except requests.RequestException as e:
            psi.logger.warning(tr('cache.exception', e))
        else:
            psi.logger.info(tr('cache.cached'))

    def save(self):
        if not os.path.isdir(os.path.dirname(self.CACHE_PATH)):
            os.makedirs(os.path.dirname(self.CACHE_PATH))
        with open(self.CACHE_PATH, 'w+') as f:
            json.dump(self.serialize(), f, indent=4, ensure_ascii=False)

    @classmethod
    def load(cls):
        if not os.path.isfile(cls.CACHE_PATH):
            return cls()
        with open(cls.CACHE_PATH, 'r') as f:
            data = json.load(f)
            return cls(plugin_amount=data['plugin_amount'], plugins=data['plugins'])


cache = Cache.load()
