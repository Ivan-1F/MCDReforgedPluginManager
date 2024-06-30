from typing import List, Optional

import requests
from mcdreforged.api.all import *

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
    asset: AssetInfo
    description: Optional[str]
    prerelease: bool


class ReleaseSummary(Serializable):
    id: str
    latest_version_index: Optional[int]
    releases: List[ReleaseInfo]

    def get_latest_release(self) -> Optional[ReleaseInfo]:
        if self.latest_version_index is not None:
            return self.releases[self.latest_version_index]
        return None
