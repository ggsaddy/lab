import os
import json
from typing import Dict, Optional, Union
from .interfaces import Subject
from .editor import TextEditor, AutoModifiedDecorator
from .memento import WorkspaceMemento, WorkspaceCaretaker
from .logger import Logger # 需要引入 Logger 类型做类型提示(可选)
from pathlib import Path
from .xml_editor import XmlEditor

class Workspace(Subject):
    def __init__(self):
        super().__init__()
        self.editors: Dict[str, Union[TextEditor, XmlEditor]] = {}
        self.active_editor_name: Optional[str] = None
        self.caretaker = WorkspaceCaretaker()
        # Logger 会在 main 中 attach，但为了获取 logger 状态，我们最好能反向访问，
        # 或者在 Subject 中保存 observers 列表。
        # 在 interfaces.py 的 Subject 中，我们有 self._observers。
        # 为了方便，我们假设第一个 observer 就是 Logger。
    
    # ... (active_editor, load_file, init_file, save_file, _write_to_disk 代码不变，请保留) ...
    # 为了节省篇幅，这里只列出修改过或新增的方法，其余请保留原样
    
    @property
    def active_editor(self) -> Optional[Union[TextEditor, XmlEditor]]:
        if self.active_editor_name and self.active_editor_name in self.editors:
            return self.editors[self.active_editor_name]
        return None

    def load_file(self, filename: str):
        if filename in self.editors:
            self.switch_editor(filename)
            return
        suffix = Path(filename).suffix
        if suffix == ".txt":
            content = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = [line.rstrip('\n') for line in f.readlines()]
                except IOError as e:
                    print(f"Error loading file: {e}")
                    return
            else:
                print(f"New file created: {filename}")
            editor = TextEditor(filename, content)
            editor = AutoModifiedDecorator(editor)
            self.editors[filename] = editor
            if self.active_editor_name:
                self.notify("active_stop", {"filename": self.active_editor_name})
            self.active_editor_name = filename
            if content and content[0].strip().startswith('# log'):
                self.notify("auto_log_enable", {"filename": filename, "log_config": content[0].strip()})
            self.notify("active_start", {"filename": filename})
            self.notify("command", {"filename": filename, "command_str": f"load {filename}"})
            print(f"Loaded {filename}")
        elif suffix == ".xml":
            xml_text = None
            first_line = None
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        raw = f.read()
                        lines = raw.splitlines()
                        if lines and lines[0].strip().startswith('# log'):
                            first_line = lines[0].strip()
                            xml_text = "\n".join(lines[1:])
                        else:
                            xml_text = raw
                except IOError as e:
                    print(f"Error loading file: {e}")
                    return
            else:
                xml_text = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<root id=\"root\"></root>"
                print(f"New file created: {filename}")
            editor = XmlEditor(filename, xml_text=xml_text, log_config_line=first_line)
            self.editors[filename] = editor
            if self.active_editor_name:
                self.notify("active_stop", {"filename": self.active_editor_name})
            self.active_editor_name = filename
            if first_line and first_line.startswith('# log'):
                self.notify("auto_log_enable", {"filename": filename, "log_config": first_line})
            self.notify("active_start", {"filename": filename})
            self.notify("command", {"filename": filename, "command_str": f"load {filename}"})
            print(f"Loaded {filename}")
        else:
            print(f"Warning: unsupported file type: {suffix}")

    def init_file(self, filename: str, with_log: bool = False):
        if filename in self.editors:
            print(f"Error: {filename} is already open.")
            return
        suffix = Path(filename).suffix
        if suffix == '.txt':
            content = ["# log"] if with_log else []
            editor = TextEditor(filename, content)
            editor = AutoModifiedDecorator(editor)
            editor.is_modified = True 
            self.editors[filename] = editor
            if self.active_editor_name:
                self.notify("active_stop", {"filename": self.active_editor_name})
            self.active_editor_name = filename
            if with_log:
                self.notify("auto_log_enable", {"filename": filename, "log_config": "# log"})
            self.notify("active_start", {"filename": filename})
            self.notify("command", {"filename": filename, "command_str": f"init {filename}"})
            print(f"Initialized {filename}")
        elif suffix == '.xml':
            first_line = "# log" if with_log else None
            xml_text = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<root id=\"root\"></root>"
            editor = XmlEditor(filename, xml_text=xml_text, log_config_line=first_line)
            editor.is_modified = True
            self.editors[filename] = editor
            if self.active_editor_name:
                self.notify("active_stop", {"filename": self.active_editor_name})
            self.active_editor_name = filename
            if with_log:
                self.notify("auto_log_enable", {"filename": filename, "log_config": first_line})
            self.notify("active_start", {"filename": filename})
            self.notify("command", {"filename": filename, "command_str": f"init {filename}"})
            print(f"Initialized {filename}")
        else:
            print(f"Warning: unsupported file type: {suffix}")

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
        if filename in self.editors:
            if self.active_editor_name and self.active_editor_name != filename:
                self.notify("active_stop", {"filename": self.active_editor_name})
            self.active_editor_name = filename
            self.notify("active_start", {"filename": filename})
            print(f"Switched to {filename}")
        else:
            print(f"Error: File {filename} not open.")
    
    def list_editors(self):
        if not self.editors:
            print("No files open.")
            return
        stat = None
        for obs in self._observers:
            if hasattr(obs, 'get_duration_str'):
                stat = obs
                break
        for name, editor in self.editors.items():
            prefix = ">" if name == self.active_editor_name else " "
            status = "*" if editor.is_modified else ""
            duration = f" ({stat.get_duration_str(name)})" if stat else ""
            print(f"{prefix} {name}{status}{duration}")

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
            try:
                choice = input(f"File '{target}' has unsaved changes. Save? (y/n): ").strip().lower()
            except EOFError:
                choice = 'n'
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
                try:
                    choice = input(f"File '{filename}' has unsaved changes. Save? (y/n): ").strip().lower()
                except EOFError:
                    choice = 'n'
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

        self.save_state()
        return True
    


    def create_memento(self) -> WorkspaceMemento:
        """创建当前状态的备忘录"""
        # 收集文件数据
        files_data = []
        for name, editor in self.editors.items():
            files_data.append({
                "name": name,
                "modified": editor.is_modified
            })
        
        # 获取日志开启状态
        logged_files = []
        if self._observers and hasattr(self._observers[0], 'get_enabled_files'):
            logged_files = self._observers[0].get_enabled_files()
        
        return WorkspaceMemento(
            active_editor=self.active_editor_name,
            files_data=files_data,
            logged_files=logged_files
        )
    
    def restore_from_memento(self, memento: WorkspaceMemento):
        """从备忘录恢复状态"""
        state = memento.get_state()
        
        # 恢复文件
        for file_data in state["files"]:
            fname = file_data["name"]
            is_modified = file_data.get("modified", False)
            
            self.load_file(fname)
            
            # 恢复修改状态
            if fname in self.editors:
                self.editors[fname].is_modified = is_modified
        
        # 恢复日志状态
        for fname in state.get("logged_files", []):
            if fname in self.editors:
                self.notify("log_on", {"filename": fname})
        # 恢复活动文件
        active = state.get("active")
        if active and active in self.editors:
            self.active_editor_name = active

    # def _save_state(self):
    #     """
    #     修复 Bug 3: 保存 modified 状态和日志开关状态
    #     """
    #     files_data = []
        
    #     # 获取日志开启状态
    #     logged_files = []
    #     if self._observers and hasattr(self._observers[0], 'get_enabled_files'):
    #         logged_files = self._observers[0].get_enabled_files()

    #     for name, editor in self.editors.items():
    #         files_data.append({
    #             "name": name,
    #             "modified": editor.is_modified,
    #             "logging_enabled": name in logged_files
    #         })

    #     state = {
    #         "active": self.active_editor_name,
    #         "files": files_data
    #     }
        
    #     try:
    #         with open(".workspace_state.json", 'w') as f:
    #             json.dump(state, f, indent=2)
    #     except IOError:
    #         pass

    # def _load_workspace_state(self):
    #     """
    #     修复 Bug 3: 恢复 modified 状态和日志开关状态
    #     """
    #     if not os.path.exists(".workspace_state.json"):
    #         return
    #     try:
    #         with open(".workspace_state.json", 'r') as f:
    #             state = json.load(f)
                
    #             file_list = state.get("files", [])
    #             # 兼容旧版本配置（如果之前只是存了 list string）
    #             if file_list and isinstance(file_list[0], str):
    #                 # 旧版本逻辑
    #                 for fname in file_list:
    #                     self.load_file(fname)
    #             else:
    #                 # 新版本逻辑
    #                 for file_data in file_list:
    #                     fname = file_data["name"]
    #                     is_modified = file_data["modified"]
    #                     logging_enabled = file_data["logging_enabled"]
                        
    #                     self.load_file(fname)
                        
    #                     # 恢复修改状态
    #                     if fname in self.editors:
    #                         self.editors[fname].is_modified = is_modified
                        
    #                     # 恢复日志状态
    #                     if logging_enabled:
    #                         self.notify("log_on", {"filename": fname})
                            
    #             # 恢复活动文件
    #             active = state.get("active")
    #             if active in self.editors:
    #                 self.active_editor_name = active
                    
    #     except (IOError, json.JSONDecodeError):
    #         print("Warning: Failed to restore workspace state.")
    def save_state(self):
        """保存当前工作区状态（公开接口）"""
        memento = self.create_memento()
        self.caretaker.save(memento)
    
    def load_workspace_state(self):
        """加载工作区状态（公开接口）"""
        memento = self.caretaker.load()
        if memento:
            self.restore_from_memento(memento)
            print("Workspace state restored.")
