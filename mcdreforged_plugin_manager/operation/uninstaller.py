import os
from typing import Iterable

from mcdreforged.api.all import *

from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.operation.task_manager import Task
from mcdreforged_plugin_manager.texts import CONFIRM_COMMAND_TEXT
from mcdreforged_plugin_manager.storage.cache import cache
from mcdreforged_plugin_manager.util.mcdr_util import unload_plugin
from mcdreforged_plugin_manager.util.translation import tr


def get_plugins_depend_on(plugin_id: str) -> Iterable[str]:
    for other_id in psi.get_plugin_list():
        try:
            other = cache.get_plugin_by_id(other_id)
        except KeyError:
            continue
        else:
            if other is None:
                continue
            if plugin_id in other.dependencies.keys():
                yield other_id


class PluginUninstaller(Task):
    def __init__(self, plugin_id: str, source: CommandSource):
        self.reply = source.reply
        self.plugin_id = plugin_id
        super().__init__()

    def _run(self):
        success = True
        path = psi.get_plugin_file_path(self.plugin_id)
        self.reply(tr('uninstaller.step.unload_plugin', self.plugin_id))
        unload_plugin(self.plugin_id)
        self.reply(tr('uninstaller.step.remove_file', path))
        os.remove(path)
        self.reply(tr('uninstaller.step.reload_mcdr'))
        psi.refresh_all_plugins()
        if success:
            self.reply(tr('uninstaller.result.success'))
        else:
            self.reply(tr('uninstaller.result.failed'))

    def init(self):
        self.reply(tr('uninstaller.dependency_warning', self.plugin_id))
        self.reply(', '.join(list(get_plugins_depend_on(self.plugin_id))))
        self.reply(tr('uninstaller.confirm', CONFIRM_COMMAND_TEXT))
