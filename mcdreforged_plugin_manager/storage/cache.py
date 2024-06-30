import json
import os
import time
from threading import Event, Thread
from typing import Callable

from mcdreforged.api.all import *

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
    CACHE_PATH = os.path.join(psi.get_data_folder(), 'everything.json')
    TMP_CACHE_PATH = os.path.join(psi.get_data_folder(), 'everything.json.tmp')

    def __init__(self):
        self.loaded = False

    @new_thread('MPMCache')
    def cache(self):
        before = self.plugin_amount

        psi.logger.info(tr('cache.cache'))

        try:
            download_file(config.source, self.TMP_CACHE_PATH)
        except Exception as e:
            psi.say(tr('cache.exception_ingame'))
            psi.logger.warning(tr('cache.exception', e))
        else:
            # remove cache if exist
            if os.path.exists(self.CACHE_PATH) and os.path.isfile(self.CACHE_PATH):
                os.remove(self.CACHE_PATH)
            os.rename(self.TMP_CACHE_PATH, self.CACHE_PATH)

            self.__load()
            psi.logger.info(tr('cache.cached', self.plugin_amount - before))

            if config.check_update:
                from mcdreforged_plugin_manager.util import upgrade_helper
                upgrade_helper.show_check_update_result(psi.logger.info)

    def __load(self):
        self.plugin_amount = 0
        self.plugins.clear()

        try:
            with open(self.CACHE_PATH, 'r', encoding='utf8') as f:
                data = json.load(f)
            
            for plugin in data['plugins'].values():
                plugin = Plugin.create(plugin)
                plugin_id = plugin.meta.id
                self.plugins[plugin_id] = plugin
                self.plugin_amount += 1
        except Exception as e:
            psi.logger.warn(tr('cache.load_failed'))
            self.loaded = False
        else:
            self.loaded = True


cache = Cache()


def clock_callback():
    cache.cache()


cache_clock = CacheClock(config.cache_interval * 60, event=clock_callback)
