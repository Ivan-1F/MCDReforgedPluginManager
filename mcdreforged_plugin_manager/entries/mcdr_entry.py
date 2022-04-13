from mcdreforged.api.all import *

from mcdreforged_plugin_manager.commands import list_plugins
from mcdreforged_plugin_manager.config import config


def on_load(server: PluginServerInterface, old):
    def get_literal(literal: str):
        return Literal(literal).requires(lambda src, ctx: src.has_permission(config.permission))
    server.register_command(
        Literal('!!mpm')
        .then(
            get_literal('list')
            .then(
                Text('labels')
                .suggests(lambda: ['information', 'tool', 'management', 'api'])
                .runs(lambda src, ctx: list_plugins(src, ctx['labels'].split(',')))
            )
        )
    )
