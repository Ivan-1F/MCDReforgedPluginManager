import functools
import os
from typing import Iterable, List

from mcdreforged.api.decorator import new_thread
from mcdreforged.command.command_source import CommandSource

from mcdreforged_plugin_manager.constants import psi, meta
from mcdreforged_plugin_manager.storage.cache import cache
from mcdreforged_plugin_manager.task.task_manager import Task, task_manager
from mcdreforged_plugin_manager.texts import CONFIRM_COMMAND_TEXT
from mcdreforged_plugin_manager.util.mcdr_util import unload_plugin
from mcdreforged_plugin_manager.util.translation_util import tr


def get_plugins_depend_on(plugin_id: str) -> Iterable[str]:
    for other_id in psi.get_plugin_list():
        try:
            other = cache.get_plugin_by_id(other_id)
        except KeyError:
            continue
        else:
            if other is None:
                continue
            if plugin_id in other.meta.dependencies.keys():
                yield other_id


class PluginUninstaller(Task):
    def __init__(self, plugin_ids: List[str], source: CommandSource):
        self.reply = source.reply
        self.plugin_ids = plugin_ids
        super().__init__()

    @new_thread('MPMUninstall')
    def run(self):
        success = True
        for plugin_id in self.plugin_ids:
            path = psi.get_plugin_file_path(plugin_id)
            self.reply(tr('uninstaller.step.unload_plugin', plugin_id))
            unload_plugin(plugin_id)
            self.reply(tr('uninstaller.step.remove_file', path))
            os.remove(path)

        self.reply(tr('uninstaller.step.reload_mcdr'))
        psi.refresh_changed_plugins()
        if success:
            self.reply(tr('uninstaller.result.success'))
        else:
            self.reply(tr('uninstaller.result.failed'))

    def init(self):
        def cmp(a: str, b: str):
            return -1 if a in list(get_plugins_depend_on(b)) else 1

        # don't operate on self (mcdreforged_plugin_manager)
        if meta.id in self.plugin_ids:
            if len(self.plugin_ids) == 1:  # ['mcdreforged_plugin_manager']
                self.reply(tr('uninstaller.cannot_uninstall_self'))
                task_manager.clear_task()
                return
            else:
                self.plugin_ids.remove(meta.id)

        # sort so plugins with no other plugin depend on will be uninstalled first
        self.plugin_ids = sorted(self.plugin_ids, key=functools.cmp_to_key(cmp))

        self.reply(tr('uninstaller.title', ', '.join(self.plugin_ids)))

        for plugin_id in self.plugin_ids:
            plugins = list(get_plugins_depend_on(plugin_id))
            plugins = [plugin for plugin in plugins if plugin not in self.plugin_ids]
            if len(plugins) > 0:
                self.reply(tr('uninstaller.dependency_warning', plugin_id))
                self.reply(', '.join(plugins))

        self.reply(tr('uninstaller.confirm', CONFIRM_COMMAND_TEXT))
