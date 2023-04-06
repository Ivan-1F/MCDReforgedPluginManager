from mcdreforged.api.rtext import *

from mcdreforged_plugin_manager import constants
from mcdreforged_plugin_manager.util.text_util import command_run
from mcdreforged_plugin_manager.util.translation_util import tr

CONFIRM_COMMAND_TEXT = command_run(
    RText(constants.PREFIX + ' confirm').set_color(RColor.gold),
    '!!mpm confirm',
    tr('installer.confirm.command_hover')
)
