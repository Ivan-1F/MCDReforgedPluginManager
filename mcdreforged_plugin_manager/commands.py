from typing import Callable, Any, Optional, Union, List
from mcdreforged.api.all import *

from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.util.cache import cache

ReplayCallback = Callable[[Any], None]


class CommandExecutor:
    def __init__(self, reply: Optional[Callable[[Any], None]] = None, tr: Callable = psi.tr):
        self.tr = tr
        self.reply = reply

    def with_source(self, source: CommandSource):
        self.reply = source.reply
        return self

    def list_plugins(self, labels: Optional[Union[type(None), str, List[str]]] = None):
        for plugin in cache.get_plugins_by_labels(labels):
            self.reply(plugin.brief)
