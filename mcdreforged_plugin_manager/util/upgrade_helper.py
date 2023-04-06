from typing import Iterator, Callable, Any, Tuple

from mcdreforged.minecraft.rtext.style import RColor, RStyle
from mcdreforged.minecraft.rtext.text import RTextBase, RTextList, RText
from mcdreforged.plugin.meta.version import Version

from mcdreforged_plugin_manager import constants
from mcdreforged_plugin_manager.constants import psi
from mcdreforged_plugin_manager.storage.cache import cache
from mcdreforged_plugin_manager.util.text_util import command_run
from mcdreforged_plugin_manager.util.translation_util import tr


def get_all_non_latest_plugins() -> Iterator[Tuple[str, Version, Version]]:
    for plugin_id in psi.get_plugin_list():
        plugin = cache.get_plugin_by_id(plugin_id)
        if plugin is None:
            continue
        result = plugin.meta.check_update()
        if not result.is_latest:
            yield plugin_id, result.latest_version, result.local_version


def show_check_update_result(reply: Callable[[RTextBase], Any]):
    updates = list(get_all_non_latest_plugins())
    if len(updates) == 0:
        reply(tr('update_helper.all_up_to_date'))
    else:
        reply(tr('update_helper.title'))
        for plugin_id, latest_version, local_version in updates:
            plugin = cache.get_plugin_by_id(plugin_id)
            reply(RTextList(command_run(RText(plugin.meta.name).set_color(RColor.yellow).set_styles(RStyle.bold),
                                        '{} info {}'.format(constants.PREFIX, plugin_id),
                                        tr('plugin.operation.show_info')),
                            ' ',
                            RText('({})'.format(plugin.meta.id)).set_color(RColor.gray)))
            reply(RTextList(RTextList(RText(local_version).set_color(RColor.gray), ' -> ',
                                      RText(latest_version).set_color(RColor.green)),
                            ' ',
                            command_run(RText('[↑]').set_color(RColor.green),
                                        '{} upgrade {}'.format(constants.PREFIX, plugin_id),
                                        tr('update_helper.click_to_upgrade', latest_version))
                            ))
