from mcdreforged.api.all import *

from mcdreforged_plugin_manager.commands import list_plugins, search, info
from mcdreforged_plugin_manager.config import config
from mcdreforged_plugin_manager.util.cache import cache, cache_clock


def register_commands(server: PluginServerInterface):
    def get_literal(literal: str):
        return Literal(literal).requires(lambda src, ctx: src.has_permission(config.permission))
    server.register_command(
        Literal('!!mpm')
        .then(
            get_literal('list')
            .runs(lambda src: list_plugins(src))
            .then(
                Text('labels')
                .suggests(lambda: ['information', 'tool', 'management', 'api'])
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
    )


def on_load(server: PluginServerInterface, old):
    if hasattr(old, 'clock'):
        cache_clock.last_update_time = old.cache_clock.last_update_time
    cache_clock.start()
    cache.cache()
    cache_clock.reset_timer()
    register_commands(server)


def on_unload(server: PluginServerInterface):
    cache_clock.stop()
