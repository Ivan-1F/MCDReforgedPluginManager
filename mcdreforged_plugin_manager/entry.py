from mcdreforged.command.builder.nodes.arguments import Text, GreedyText
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.plugin.server_interface import PluginServerInterface

from mcdreforged_plugin_manager import constants
from mcdreforged_plugin_manager.commands import show_help_message, info, list_plugins, search, install, uninstall, \
    upgrade, check_update
from mcdreforged_plugin_manager.config import config
from mcdreforged_plugin_manager.constants import PLUGIN_LABELS, psi, meta
from mcdreforged_plugin_manager.storage.cache import cache, cache_clock
from mcdreforged_plugin_manager.task.task_manager import task_manager
from mcdreforged_plugin_manager.util.translation_util import tr


def register_commands(server: PluginServerInterface):
    def get_literal(literal: str):
        return Literal(literal).requires(lambda src, ctx: src.has_permission(config.permission),
                                         lambda: tr('permission_denied'))

    server.register_command(
        Literal(constants.PREFIX)
        .runs(show_help_message)
        .then(
            get_literal('list')
            .runs(lambda src: list_plugins(src))
            .then(
                Text('labels')
                .suggests(lambda: PLUGIN_LABELS)
                .runs(lambda src, ctx: list_plugins(src, ctx['labels'].split(',')))
            )
        )
        .then(
            get_literal('search')
            .then(
                GreedyText('query')
                .runs(lambda src, ctx: search(src, ctx['query']))
            )
        )
        .then(
            get_literal('info')
            .then(
                Text('plugin_id')
                .suggests(cache.get_plugin_ids)
                .runs(lambda src, ctx: info(src, ctx['plugin_id']))
            )
        )
        .then(
            get_literal('install')
            .then(
                GreedyText('plugin_ids')
                .suggests(lambda: [plugin_id for plugin_id in cache.get_plugin_ids() if plugin_id != meta.id])
                .runs(lambda src, ctx: install(src, ctx['plugin_ids'].split(' ')))
            )
        )
        .then(
            get_literal('upgrade')
            .then(
                GreedyText('plugin_ids')
                .suggests(lambda: [plugin_id for plugin_id in psi.get_plugin_list() if plugin_id != meta.id])
                .runs(lambda src, ctx: upgrade(src, ctx['plugin_ids'].split(' ')))
            )
        )
        .then(
            get_literal('uninstall')
            .then(
                GreedyText('plugin_ids')
                .suggests(lambda: [plugin_id for plugin_id in psi.get_plugin_list() if plugin_id != meta.id])
                .runs(lambda src, ctx: uninstall(src, ctx['plugin_ids'].split(' ')))
            )
        )
        .then(
            get_literal('confirm')
            .runs(task_manager.on_confirm)
        )
        .then(
            get_literal('checkupdate')
            .runs(check_update)
        )
    )


def on_load(server: PluginServerInterface, old):
    if hasattr(old, 'cache_clock'):
        cache_clock.last_update_time = old.cache_clock.last_update_time
    cache_clock.start()
    cache.load()
    register_commands(server)
    server.register_help_message(constants.PREFIX, tr('help_summary'))


def on_unload(server: PluginServerInterface):
    cache_clock.stop()
