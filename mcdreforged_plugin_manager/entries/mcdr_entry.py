from mcdreforged.api.all import *

from mcdreforged_plugin_manager.commands import CommandExecutor
from mcdreforged_plugin_manager.config import config

command_executor = CommandExecutor()


def on_load(server: PluginServerInterface, old):
    def get_literal(literal: str):
        return Literal(literal).requires(lambda src, ctx: src.has_permission(config.permission))
    server.register_command(
        Literal('!!mpm')
        .then(
            get_literal('list')
            .then(
                Text('labels')
                .runs(lambda src, ctx: command_executor.with_source(src).list_plugins(ctx['labels'].split(',')))
            )
        )
    )
