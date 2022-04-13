from typing import Optional, Union, List
from mcdreforged.api.all import *

from mcdreforged_plugin_manager.util.cache import cache


def list_plugins(source: CommandSource, labels: Optional[Union[type(None), str, List[str]]] = None):
    for plugin in cache.get_plugins_by_labels(labels):
        source.reply(plugin.brief)
