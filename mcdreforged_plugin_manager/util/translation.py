from mcdreforged.translation.translation_text import RTextMCDRTranslation

from mcdreforged_plugin_manager.constants import psi, meta


def tr(key: str, *args, **kwargs) -> RTextMCDRTranslation:
    return psi.rtr('{}.{}'.format(meta.id, key), *args, **kwargs)
