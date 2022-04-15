from mcdreforged.api.rtext import *

from mcdreforged_plugin_manager.util.text_util import command_run
from mcdreforged_plugin_manager.util.translation import tr

CONFIRM_COMMAND_TEXT = command_run(RText('!!mpm confirm').set_color(RColor.gold), '!!mpm confirm', tr('installer.confirm.command_hover'))
