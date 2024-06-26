import functools
from typing import Callable, List, Union, Optional

from mcdreforged.api.all import *

from mcdreforged_plugin_manager.constants import meta, PREFIX
from mcdreforged_plugin_manager.storage.cache import cache
from mcdreforged_plugin_manager.task.install_task import PluginInstaller
from mcdreforged_plugin_manager.task.task_manager import task_manager
from mcdreforged_plugin_manager.task.uninstall_task import PluginUninstaller
from mcdreforged_plugin_manager.util.mcdr_util import is_plugin_loaded
from mcdreforged_plugin_manager.util.translation_util import tr
from mcdreforged_plugin_manager.util.upgrade_helper import show_check_update_result


def ensure_cache_loaded(func: Callable):
    """
    A decorator that ensures the cache is loaded
    """
    @functools.wraps(func)
    def wrapper(source: CommandSource, *args, **kwargs):
        if not cache.loaded:
            source.reply(tr('cache.not_loaded'))
        func(source, *args, **kwargs)

    return wrapper


def ensure_plugin_id(func: Callable):
    """
    A decorator that ensures the plugin id(s) in the function parameter is present in the cache
    """
    @functools.wraps(func)
    def wrapper(source: CommandSource, plugin_id_input: Union[str, List[str]], *args, **kwargs):
        plugin_ids = [plugin_id_input] if isinstance(plugin_id_input, str) else plugin_id_input
        for plugin_id in plugin_ids:
            if not cache.is_plugin_present(plugin_id):
                source.reply(tr('plugin.not_found', plugin_id))
                return
        func(source, plugin_id_input, *args, **kwargs)

    return wrapper


def ensure_plugin_installed(func: Callable):
    """
    A decorator that ensures the plugin id(s) in the function parameter is installed
    """
    @functools.wraps(func)
    def wrapper(source: CommandSource, plugin_id_input: Union[str, List[str]], *args, **kwargs):
        plugin_ids = [plugin_id_input] if isinstance(plugin_id_input, str) else plugin_id_input
        for plugin_id in plugin_ids:
            if not is_plugin_loaded(plugin_id):
                source.reply(tr('plugin.not_installed', plugin_id))
                return
        func(source, plugin_id_input, *args, **kwargs)

    return wrapper


def show_help_message(source: CommandSource):
    source.reply(tr('help_message', prefix=PREFIX, name=meta.name, version=meta.version))


@ensure_cache_loaded
def list_plugins(source: CommandSource, labels: Optional[Union[None, str, List[str]]] = None):
    plugins = list(cache.get_plugins_by_labels(labels))
    for plugin in plugins:
        source.reply(plugin.meta.brief)
        source.reply('')
    if len(plugins) == 0:
        source.reply(tr('list.empty'))


@ensure_cache_loaded
def search(source: CommandSource, query: str):
    plugins = list(cache.search(query))
    for plugin in plugins:
        source.reply(plugin.meta.brief)
        source.reply('')
    if len(plugins) == 0:
        source.reply(tr('list.empty'))


@ensure_cache_loaded
@ensure_plugin_id
def info(source: CommandSource, plugin_id: str):
    source.reply(cache.get_plugin_by_id(plugin_id).meta.detail)


@ensure_cache_loaded
@ensure_plugin_id
def install(source: CommandSource, plugin_ids: List[str]):
    installer = PluginInstaller(plugin_ids, source, upgrade=False)
    task_manager.manage_task(installer)


@ensure_cache_loaded
@ensure_plugin_installed
@ensure_plugin_id
def upgrade(source: CommandSource, plugin_ids: List[str]):
    installer = PluginInstaller(plugin_ids, source, upgrade=True)
    task_manager.manage_task(installer)


@ensure_cache_loaded
@ensure_plugin_installed
def uninstall(source: CommandSource, plugin_ids: List[str]):
    uninstaller = PluginUninstaller(plugin_ids, source)
    task_manager.manage_task(uninstaller)


@ensure_cache_loaded
def check_update(source: CommandSource):
    show_check_update_result(source.reply)
