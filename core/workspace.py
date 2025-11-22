import os
import json
from typing import Dict, Optional
from .interfaces import Subject
from .editor import TextEditor
from .logger import Logger # 需要引入 Logger 类型做类型提示(可选)
from pathlib import Path

class Workspace(Subject):
    def __init__(self):
        super().__init__()
        self.editors: Dict[str, TextEditor] = {}
        self.active_editor_name: Optional[str] = None
        # Logger 会在 main 中 attach，但为了获取 logger 状态，我们最好能反向访问，
        # 或者在 Subject 中保存 observers 列表。
        # 在 interfaces.py 的 Subject 中，我们有 self._observers。
        # 为了方便，我们假设第一个 observer 就是 Logger。
    
    # ... (active_editor, load_file, init_file, save_file, _write_to_disk 代码不变，请保留) ...
    # 为了节省篇幅，这里只列出修改过或新增的方法，其余请保留原样
    
    @property
    def active_editor(self) -> Optional[TextEditor]:
        if self.active_editor_name and self.active_editor_name in self.editors:
            return self.editors[self.active_editor_name]
        return None

    def load_file(self, filename: str):
        # (保持原样)
        if filename in self.editors:
            self.switch_editor(filename)
            return
        content = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = [line.rstrip('\n') for line in f.readlines()]
            except IOError as e:
                print(f"Error loading file: {e}")
                return
        else:
            if Path(filename).suffix != '.txt':
                print(f"Warning: {filename} is not a .txt file.Please check the file format.")
                return 

            print(f"New file created: {filename}")
            
        editor = TextEditor(filename, content)
        self.editors[filename] = editor
        self.active_editor_name = filename
        
        if content and content[0].strip() == "# log":
            self.notify("auto_log_enable", {"filename": filename})

        self.notify("command", {"filename": filename, "command_str": f"load {filename}"})
        print(f"Loaded {filename}")

    def init_file(self, filename: str, with_log: bool = False):
        # (保持原样)
        if filename in self.editors:
            print(f"Error: {filename} is already open.")
            return
        if Path(filename).suffix != '.txt':
            print(f"Warning: {filename} is not a .txt file.Please check the file format.")
            return
        content = ["# log"] if with_log else []
        editor = TextEditor(filename, content)
        editor.is_modified = True 
        self.editors[filename] = editor
        self.active_editor_name = filename
        if with_log:
            self.notify("auto_log_enable", {"filename": filename})
        self.notify("command", {"filename": filename, "command_str": f"init {filename}"})
        print(f"Initialized {filename}")

    def save_file(self, filename: str = None):
        # (保持原样)
        if filename == "all":
            for name in self.editors:
                self._write_to_disk(name)
            return
        target = filename if filename else self.active_editor_name
        if not target or target not in self.editors:
            print("Error: No file specified or file not open.")
            return
        self._write_to_disk(target)

    def _write_to_disk(self, filename: str):
        # (保持原样)
        editor = self.editors[filename]
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(editor.get_content_str())
            editor.is_modified = False
            self.notify("command", {"filename": filename, "command_str": "save"})
            print(f"Saved {filename}")
        except IOError as e:
            print(f"Error saving {filename}: {e}")

    def switch_editor(self, filename: str):
        # (保持原样)
        if filename in self.editors:
            self.active_editor_name = filename
            print(f"Switched to {filename}")
        else:
            print(f"Error: File {filename} not open.")
    
    def list_editors(self):
        # (保持原样)
        if not self.editors:
            print("No files open.")
            return
        for name, editor in self.editors.items():
            prefix = ">" if name == self.active_editor_name else " "
            status = "*" if editor.is_modified else ""
            print(f"{prefix} {name}{status}")

    # === 以下是重点修改的部分 ===

    def close_file(self, filename: str = None):
        """
        修复 Bug 2: 如果用户选择不保存，且文件在磁盘不存在(纯buffer)，则视为废弃
        """
        target = filename if filename else self.active_editor_name
        if not target or target not in self.editors:
            print("Error: File not open.")
            return

        editor = self.editors[target]
        
        if editor.is_modified:
            choice = input(f"File '{target}' has unsaved changes. Save? (y/n): ").strip().lower()
            if choice == 'y':
                self._write_to_disk(target)
            else:
                # 用户选择不保存
                # Bug 2 修复逻辑: 如果是 init 产生的并且从未保存过（磁盘上无此文件）
                if not os.path.exists(target):
                    # 清理日志（需要通知 logger 或直接调用）
                    # 这里我们通过 hack 方式获取 logger，或者发送特殊事件
                    # 简单起见，假设第一个 observer 是 logger (在 main 中 attach 的)
                    if self._observers:
                        logger = self._observers[0] 
                        if hasattr(logger, 'delete_log_file'):
                            logger.delete_log_file(target)
        
        del self.editors[target]
        self.notify("command", {"filename": target, "command_str": "close"})
        print(f"Closed {target}")

        if self.active_editor_name == target:
            self.active_editor_name = list(self.editors.keys())[-1] if self.editors else None
            if self.active_editor_name:
                print(f"Active file switched to {self.active_editor_name}")

    def check_and_exit(self) -> bool:
        open_files = list(self.editors.keys())
        
        for filename in open_files:
            editor = self.editors[filename]
            if editor.is_modified:
                choice = input(f"File '{filename}' has unsaved changes. Save? (y/n): ").strip().lower()
                if choice == 'y':
                    self._write_to_disk(filename)
                else:
                    if not os.path.exists(filename):
                        if self._observers:
                            logger = self._observers[0]
                            if hasattr(logger, 'delete_log_file'):
                                logger.delete_log_file(filename)
             
                        del self.editors[filename] 
                        
                        if self.active_editor_name == filename:
                            self.active_editor_name = None

        self._save_state()
        return True

    def _save_state(self):
        """
        修复 Bug 3: 保存 modified 状态和日志开关状态
        """
        files_data = []
        
        # 获取日志开启状态
        logged_files = []
        if self._observers and hasattr(self._observers[0], 'get_enabled_files'):
            logged_files = self._observers[0].get_enabled_files()

        for name, editor in self.editors.items():
            files_data.append({
                "name": name,
                "modified": editor.is_modified,
                "logging_enabled": name in logged_files
            })

        state = {
            "active": self.active_editor_name,
            "files": files_data
        }
        
        try:
            with open(".workspace_state.json", 'w') as f:
                json.dump(state, f, indent=2)
        except IOError:
            pass

    def _load_workspace_state(self):
        """
        修复 Bug 3: 恢复 modified 状态和日志开关状态
        """
        if not os.path.exists(".workspace_state.json"):
            return
        try:
            with open(".workspace_state.json", 'r') as f:
                state = json.load(f)
                
                file_list = state.get("files", [])
                # 兼容旧版本配置（如果之前只是存了 list string）
                if file_list and isinstance(file_list[0], str):
                    # 旧版本逻辑
                    for fname in file_list:
                        self.load_file(fname)
                else:
                    # 新版本逻辑
                    for file_data in file_list:
                        fname = file_data["name"]
                        is_modified = file_data["modified"]
                        logging_enabled = file_data["logging_enabled"]
                        
                        self.load_file(fname)
                        
                        # 恢复修改状态
                        if fname in self.editors:
                            self.editors[fname].is_modified = is_modified
                        
                        # 恢复日志状态
                        if logging_enabled:
                            self.notify("log_on", {"filename": fname})
                            
                # 恢复活动文件
                active = state.get("active")
                if active in self.editors:
                    self.active_editor_name = active
                    
        except (IOError, json.JSONDecodeError):
            print("Warning: Failed to restore workspace state.")
