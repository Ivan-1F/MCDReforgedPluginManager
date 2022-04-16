import functools
from typing import Optional, Union, List, Callable
from mcdreforged.api.all import *

from mcdreforged_plugin_manager.constants import meta
from mcdreforged_plugin_manager.operation.installer import PluginInstaller
from mcdreforged_plugin_manager.operation.task_manager import task_manager
from mcdreforged_plugin_manager.operation.uninstaller import PluginUninstaller
from mcdreforged_plugin_manager.storage.cache import cache
from mcdreforged_plugin_manager.util.mcdr_util import is_plugin_loaded
from mcdreforged_plugin_manager.util.translation import tr
from mcdreforged_plugin_manager.util.update_helper import show_check_update_result


def ensure_plugin_id(func: Callable):
    @functools.wraps(func)
    def wrapper(source: CommandSource, plugin_id: str, *args, **kwargs):
        if not cache.is_plugin_present(plugin_id):
            source.reply(tr('plugin.not_found', plugin_id))
            return
        func(source, plugin_id, *args, **kwargs)

    return wrapper


def ensure_plugin_installed(func: Callable):
    @functools.wraps(func)
    def wrapper(source: CommandSource, plugin_id: str, *args, **kwargs):
        if not is_plugin_loaded(plugin_id):
            source.reply(tr('plugin.not_installed', plugin_id))
            return
        func(source, plugin_id, *args, **kwargs)

    return wrapper


def show_help_message(source: CommandSource):
    source.reply(tr('help_message', prefix='!!mpm', name=meta.name, version=meta.version))


def list_plugins(source: CommandSource, labels: Optional[Union[type(None), str, List[str]]] = None):
    for plugin in cache.get_plugins_by_labels(labels):
        source.reply(plugin.brief)
        source.reply('')


def search(source: CommandSource, query: str):
    for plugin in cache.search(query):
        source.reply(plugin.brief)
        source.reply('')


@ensure_plugin_id
def info(source: CommandSource, plugin_id: str):
    source.reply(cache.get_plugin_by_id(plugin_id).detail)


@ensure_plugin_id
def install(source: CommandSource, plugin_id: str):
    installer = PluginInstaller(plugin_id, source, upgrade=False)
    task_manager.manage_task(installer)


@ensure_plugin_installed
@ensure_plugin_id
def upgrade(source: CommandSource, plugin_id: str):
    installer = PluginInstaller(plugin_id, source, upgrade=True)
    task_manager.manage_task(installer)


@ensure_plugin_installed
def uninstall(source: CommandSource, plugin_id: str):
    uninstaller = PluginUninstaller(plugin_id, source)
    task_manager.manage_task(uninstaller)


def check_update(source: CommandSource):
    show_check_update_result(source.reply)
