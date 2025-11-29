# Lab 文本/XML 编辑器

- 启动：`python3 lab/main.py`
- 退出：交互中输入 `exit`
- 命令大全：交互中输入 `help`，或查看 `lab/tasklist.md`

## 程序框架
- 入口：`lab/main.py`
- 工作区：`core/workspace.py`（管理文件、事件与状态持久化）
- 文本编辑器与命令：`core/editor.py`、`core/commands.py`
- XML编辑器与命令：`core/xml_editor.py`、`core/xml_commands.py`
- 日志模块：`core/logger.py`（`# log` 自动启用，`# log -e <cmd>` 过滤）
- 编辑时长统计：`core/statistics.py`（`editor-list` 显示会话内时长）
- 拼写检查适配器：`core/spellcheck.py`（支持离线与HTTP）
- 目录树与帮助：`utils/file_helper.py`

## 常用命令类别
- 工作区：`load`、`save`、`init`、`close`、`edit`、`editor-list`、`dir-tree`、`undo`、`redo`
- 文本编辑：`append`、`insert`、`delete`、`replace`、`show`
- XML编辑：`insert-before`、`append-child`、`edit-id`、`edit-text`、`delete`、`xml-tree`
- 拼写检查：`spell-check [file]`
- 日志：`log-on`、`log-off`、`log-show`

## 拼写检查
- 默认离线（内置少量词典），可启用HTTP：
  - `LANGTOOL_HTTP=1 python3 lab/main.py`

## 测试
- 运行综合测试：`python3 lab/test/test_lab2.py`
