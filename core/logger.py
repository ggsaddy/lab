import os  # 新增引入
import datetime
from typing import Set
from .interfaces import Observer

class Logger(Observer):
    """
    日志观察者
    """
    def __init__(self):
        self.enabled_files: Set[str] = set()
        self.filters = {}

    def enable_log(self, filename: str):
        self.enabled_files.add(filename)
        # print(f"Logging enabled for {filename}") # 减少一些干扰输出

    def disable_log(self, filename: str):
        if filename in self.enabled_files:
            self.enabled_files.remove(filename)

    def get_enabled_files(self) -> list:
        """获取当前开启日志的文件列表 (用于持久化保存)"""
        return list(self.enabled_files)

    def delete_log_file(self, filename: str):
        """Bug2修复: 删除指定文件的日志(用于废弃新文件时清理)"""
        base = os.path.basename(filename)
        log_filename = f".{base}.log"
        if os.path.exists(log_filename):
            try:
                os.remove(log_filename)
                print(f"Log file removed: {log_filename}")
            except OSError as e:
                print(f"Warning: Could not delete log file: {e}")

    def _write_log(self, filename: str, message: str):
        base = os.path.basename(filename)
        log_filename = f".{base}.log"
        timestamp = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
        entry = f"{timestamp} {message}\n"
        
        try:
            with open(log_filename, 'a', encoding='utf-8') as f:
                f.write(entry)
        except IOError as e:
            print(f"Warning: Failed to write log for {filename}: {e}")

    def update(self, event_type: str, data: dict):
        filename = data.get('filename')
        if not filename:
            return

        if event_type == 'auto_log_enable':
            self.enable_log(filename)
            # 解析可能的过滤配置
            cfg = data.get('log_config')
            if cfg and '-e' in cfg:
                try:
                    parts = cfg.split()
                    excluded = []
                    for i, p in enumerate(parts):
                        if p == '-e' and i + 1 < len(parts):
                            excluded.append(parts[i+1])
                    self.filters[filename] = set(excluded)
                except Exception:
                    pass
            self._write_log(filename, "session start at " + datetime.datetime.now().strftime("%Y%m%d %H:%M:%S"))
            return

        if event_type == 'log_on':
            self.enable_log(filename)
            return
        elif event_type == 'log_off':
            self.disable_log(filename)
            return

        if event_type == 'command' and filename in self.enabled_files:
            command_str = data.get('command_str', '')
            # 过滤被排除的命令
            excluded = self.filters.get(filename)
            if excluded:
                # 命令名为首个token
                cmd_name = command_str.split()[0] if command_str else ''
                if cmd_name in excluded:
                    return
            self._write_log(filename, command_str)
