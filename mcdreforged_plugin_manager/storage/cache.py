import json
import os
import time
from threading import Thread, Event
from typing import Callable

import requests
from mcdreforged.api.all import *

from mcdreforged_plugin_manager.config import config
from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.storage.plugin import PluginMetaInfoStorage
from mcdreforged_plugin_manager.util.translation import tr


class CacheClock(Thread):
    def __init__(self, interval: int, event: Callable) -> None:
        super().__init__()
        self.setDaemon(True)
        self.setName(self.__class__.__name__)
        self.interval = interval
        self.event = event
        self.last_update_time = time.time()
        self.__stop_event = Event()
        self.__stop_flag = False

    def reset_timer(self):
        self.last_update_time = time.time()

    def run(self):
        psi.logger.info(tr('cache.clock.started', self.interval))
        while True:
            while True:
                if self.__stop_event.wait(1):
                    return
                if time.time() - self.last_update_time > self.interval:
                    break
            self.event()
            self.reset_timer()

    def stop(self):
        self.__stop_event.set()


class Cache(PluginMetaInfoStorage):
    CACHE_PATH = os.path.join(psi.get_data_folder(), 'cache.json')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @new_thread('mpm-cache')
    def cache(self):
        before = self.plugin_amount
        try:
            psi.logger.info(tr('cache.cache'))
            data = requests.get(config.get_source + '/plugins.json', timeout=config.timeout, proxies=config.proxy).json()
            self.update_from(data)
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
    def load(cls) -> 'Cache':
        if not os.path.isfile(cls.CACHE_PATH):
            obj = cls()
        else:
            with open(cls.CACHE_PATH, 'r') as f:
                data = json.load(f)
                obj = cls.deserialize(data)
        return obj


cache = Cache.load()


def clock_callback():
    cache.cache()
    if config.check_update:
        from mcdreforged_plugin_manager.util import update_helper
        update_helper.show_check_update_result(psi.logger.info)


cache_clock = CacheClock(config.cache_interval * 60, event=clock_callback)
