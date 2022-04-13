import json
import os
import traceback
from typing import List, Dict, Optional, Union, Generator

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

    @property
    def brief(self):
        return RTextList(
            RText('- '),
            RText(self.name),
            RText(' ({}@{})'.format(self.id, self.version), RColor.gray),
            '\n',
            RText('By ' + ', '.join(self.authors)),
            '\n',
            RText(self.translated_description)
        )


class PluginMetaInfoStorage(Serializable):
    plugin_amount: int = 0
    plugins: Dict[str, MetaInfo] = {}  # plugin id -> plugin meta

    def get_plugins_by_labels(self, labels: Optional[Union[type(None), str, List[str]]] = None):
        if labels is None:
            labels = ['information', 'tool', 'management', 'api']
        if isinstance(labels, str):
            labels = [labels]
        for plugin in self.plugins.values():
            if any([label in labels for label in plugin.labels]):
                yield plugin

    def search(self, query: str):
        for plugin in self.plugins.values():
            if query in plugin.name or query in plugin.id:
                yield plugin


class Cache(PluginMetaInfoStorage):
    CACHE_PATH = os.path.join(psi.get_data_folder(), 'cache.json')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if traceback.extract_stack()[-2][2] == 'load':  # only cache when initializing by Cache#load
            self.cache()

    @new_thread('mpm-cache')
    def cache(self):
        try:
            psi.logger.info(tr('cache.cache'))
            data = requests.get(config.source).json()
            self.update_from(data)
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
            obj = cls.deserialize(data)
            obj.cache()
            return obj


cache = Cache.load()
