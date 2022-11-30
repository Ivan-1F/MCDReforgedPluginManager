import requests

from mcdreforged_plugin_manager.config import config


def download_file(url: str, path: str):
    data = requests.get(url, timeout=config.timeout, proxies=config.request_proxy)
    with open(path, 'wb') as f:
        for chunk in data.iter_content():
            if chunk is not None:
                f.write(chunk)
