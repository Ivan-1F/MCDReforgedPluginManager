from mcdreforged.api.all import *

from mcdreforged_plugin_manager.commands import list_plugins, search, info
from mcdreforged_plugin_manager.config import config
from mcdreforged_plugin_manager.util.cache import cache


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
    )


def on_load(server: PluginServerInterface, old):
    register_commands(server)
