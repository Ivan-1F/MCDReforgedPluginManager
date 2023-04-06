import json
import os
import time
from threading import Event, Thread
from typing import Callable

from mcdreforged.api.decorator import new_thread

from mcdreforged_plugin_manager.config import config
from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.storage.plugin import PluginStorage, Plugin
from mcdreforged_plugin_manager.util.file_util import unzip
from mcdreforged_plugin_manager.util.network_util import download_file
from mcdreforged_plugin_manager.util.translation_util import tr


class CacheClock(Thread):
    def __init__(self, interval: int, event: Callable) -> None:
        super().__init__()
        self.setDaemon(True)
        self.setName('MPMCacheClock')
        self.interval = interval
        self.event = event
        self.last_update_time = time.monotonic()
        self.__stop_event = Event()

    def reset_timer(self):
        self.last_update_time = time.monotonic()

    def run(self):
        self.__stop_event.clear()
        psi.logger.info(tr('cache.clock.started', self.interval))
        while True:
            while True:
                if self.__stop_event.wait(1):
                    return
                if time.monotonic() - self.last_update_time > self.interval:
                    break
            self.event()
            self.reset_timer()

    def stop(self):
        self.__stop_event.set()


class Cache(PluginStorage):
    CACHE_PATH = psi.get_data_folder()

    @new_thread('MPMCache')
    def cache(self):
        before = self.plugin_amount

        psi.logger.info(tr('cache.cache'))
        zip_path = os.path.join(self.CACHE_PATH, 'meta.zip')

        try:
            download_file(config.source, zip_path)
            unzip(zip_path, self.CACHE_PATH)
        except Exception as e:
            psi.logger.warning(tr('cache.exception', e))
        else:
            os.remove(zip_path)
            self.load()
            psi.logger.info(tr('cache.cached', self.plugin_amount - before))

            if config.check_update:
                from mcdreforged_plugin_manager.util import upgrade_helper
                upgrade_helper.show_check_update_result(psi.logger.info)

    def load(self):
        self.plugin_amount = 0
        self.plugins.clear()

        meta_path = os.path.join(self.CACHE_PATH, 'PluginCatalogue-meta')
        for plugin_path, _, _ in os.walk(meta_path):
            def load_plugin_file(filename: str):
                with open(os.path.join(plugin_path, filename), 'r', encoding='utf8') as f:
                    return json.load(f)

            if plugin_path == meta_path:
                continue

            plugin_json = load_plugin_file('plugin.json')
            meta_json = load_plugin_file('meta.json')
            release_json = load_plugin_file('release.json')

            plugin = Plugin.create(plugin_json, meta_json, release_json)
            plugin_id = meta_json['id']
            self.plugins[plugin_id] = plugin
            self.plugin_amount += 1


cache = Cache()


def clock_callback():
    cache.cache()


cache_clock = CacheClock(config.cache_interval * 60, event=clock_callback)
