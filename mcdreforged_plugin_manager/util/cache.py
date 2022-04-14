import json
import os
import traceback

import requests
from mcdreforged.api.all import *

from mcdreforged_plugin_manager.config import config
from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.util.storage import PluginMetaInfoStorage, ReleaseSummary
from mcdreforged_plugin_manager.util.translation import tr


class Cache(PluginMetaInfoStorage):
    CACHE_PATH = os.path.join(psi.get_data_folder(), 'cache.json')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if traceback.extract_stack()[-2][2] == 'load':  # only cache when initializing by Cache#load
            self.cache()

    @new_thread('mpm-cache')
    def cache(self):
        before = self.plugin_amount
        try:
            psi.logger.info(tr('cache.cache'))
            data = requests.get(config.get_source + '/plugins.json', timeout=config.timeout).json()
            self.update_from(data)
            if config.cache_releases.enabled:
                for plugin in self.plugins.values():
                    if config.cache_releases.show_log:
                        psi.logger.info(tr('cache.release.cache', plugin.id))
                    plugin.release_summary = ReleaseSummary.of(plugin.id)
            self.save()
        except requests.RequestException as e:
            psi.logger.warning(tr('cache.exception', e))
        else:
            psi.logger.info(tr('cache.cached', self.plugin_amount - before))

    def save(self):
        if not os.path.isdir(os.path.dirname(self.CACHE_PATH)):
            os.makedirs(os.path.dirname(self.CACHE_PATH))
        with open(self.CACHE_PATH, 'w+') as f:
            json.dump(self.serialize(), f, indent=4, ensure_ascii=False)

    @classmethod
    def load(cls):
        if not os.path.isfile(cls.CACHE_PATH):
            obj = cls()
        else:
            with open(cls.CACHE_PATH, 'r') as f:
                data = json.load(f)
                obj = cls.deserialize(data)
        obj.cache()
        return obj


cache = Cache.load()
