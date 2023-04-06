from typing import List, Optional

import requests
from mcdreforged.utils.serializer import Serializable

from mcdreforged_plugin_manager.config import config


class AssetInfo(Serializable):
    name: str
    size: int
    download_count: int
    created_at: str
    browser_download_url: str


class ReleaseInfo(Serializable):
    url: str
    name: str
    tag_name: str
    created_at: str
    assets: List[AssetInfo]
    description: str
    prerelease: bool

    def get_mcdr_assets(self) -> List[AssetInfo]:
        return [asset for asset in self.assets if asset.name.endswith('.mcdr') or asset.name.endswith('.pyz')]


class ReleaseSummary(Serializable):
    id: str
    latest_version: str
    releases: List[ReleaseInfo]

    def get_latest_release(self) -> Optional[ReleaseInfo]:
        if len(self.releases) > 0:
            return self.releases[0]
        return None
