import functools
from typing import Optional, Union, List, Callable
from mcdreforged.api.all import *

from mcdreforged_plugin_manager.util.cache import cache
from mcdreforged_plugin_manager.util.translation import tr


def ensure_plugin_id(func: Callable):
    @functools.wraps(func)
    def wrapper(source: CommandSource, plugin_id: str, *args, **kwargs):
        if not cache.is_plugin_present(plugin_id):
            source.reply(tr('plugin.not_found', plugin_id))
            return
        func(source, plugin_id, *args, **kwargs)

    return wrapper


def list_plugins(source: CommandSource, labels: Optional[Union[type(None), str, List[str]]] = None):
    for plugin in cache.get_plugins_by_labels(labels):
        source.reply(plugin.brief)
        source.reply('')


def search(source: CommandSource, query: str):
    for plugin in cache.search(query):
        source.reply(plugin.brief)


@ensure_plugin_id
def info(source: CommandSource, plugin_id: str):
    source.reply(cache.get_plugin_by_id(plugin_id).detail)
