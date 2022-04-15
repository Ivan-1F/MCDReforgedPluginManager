import os

from mcdreforged_plugin_manager.constants import psi


def is_plugin_loaded(plugin_id: str):
    return plugin_id in psi.get_plugin_list()


def unload_plugin(plugin_id: str):
    psi.unload_plugin(plugin_id)


def remove_plugin_file(plugin_id: str):
    os.remove(psi.get_plugin_file_path(plugin_id))
