MCDReforgedPluginManager
-----

**English** | [中文](./README_cn.md)

> Manage your mcdreforged plugins with ease

MCDReforgedPluginManager (short for `mpm`) is a MCDReforged plugin manager based on [PluginCatalogue](https://github.com/MCDReforged/PluginCatalogue)

MCDReforgedPluginManager fetch plugin metadata from [PluginCatalogue](https://github.com/MCDReforged/PluginCatalogue) and update automatically at regular intervals

## Features

- Dependency checking
- Update checking
- Plugin installation & uninstallation
- Plugin upgrading
- Plugin searching

## Requirements

- [MCDReforged](https://github.com/Fallen-Breath/MCDReforged) >=2.0.0

## Configuration

The configuration file is `config/mcdreforged_plugin_manager/config.json`

The commented default config file will be generated when mpm is loaded for the first time:

```yaml
# Configure file for MCDReforgedPluginManager


# The minimum permission level to use MPM commands
# 使用 MCDReforgedPluginManager 指令的最低权限
permission: 4

# The source of plugin catalogue to fetch data
# 插件仓库数据源
# Options 选项:
# - https://raw.githubusercontent.com/MCDReforged/PluginCatalogue/meta
# - https://cdn.jsdelivr.net/gh/MCDReforged/PluginCatalogue@meta
source: https://cdn.jsdelivr.net/gh/MCDReforged/PluginCatalogue@meta

# The timeout for network requests
# 网络请求的超时时间
timeout: 5

# The time interval between each cache (unit: minute)
# 定时更新插件索引的时间间隔（单位：分钟）
cache_interval: 2

# If set to true, the plugin will check plugin updates after each scheduled cache
# 若设为 true，插件将在每次定时更新插件索引后自动检查更新
check_update: true
```

Follow the comments and modify the config, use `!!MCDR plg reload mcdreforged_plugin_manager` to reload the config

## Commands

- `!!mpm`: Display MPM help message
- `!!mpm list [labels]`: List all the plugins. If labels is specified, only plugins with specified labels will be displayed
  `labels` can be a single label or multiple labels split by `,`. Accepted labels: `information`, `tool`, `management`, `api`
- `!!mpm search <query>`: Search plugins based on the keyword
- `!!mpm info <plugin_id>`: Show detailed information of a plugin
- `!!mpm install <plugin_id>`: Install a plugin, as well as its plugin dependencies and its required python packages
- `!!mpm uninstall <plugin_id>`: Uninstall a plugin
- `!!mpm upgrade <plugin_id>`: Upgrade a plugin to the latest version
- `!!mpm confirm`: Confirm the operation
- `!!mpm checkupdate`: Manually check update for all installed plugins