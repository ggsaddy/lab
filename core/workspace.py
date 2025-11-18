'''工作区模块实现'''
from core.memento import WorkspaceMemento
from core.observer import Subject
from core.text_editor import TextEditor
from utils import load_json, save_json
import os
'''工作区状态保存路径'''
STATE_PATH = os.path.join("data", "workspace_state.json")

class Workspace(Subject):
    def __init__(self):
        super().__init__()
        self.editors = {}  # 文件名到TextEditor对象的映射集合
        self.active_file = None  # 当前活跃文件名
        self.log_enabled = False  # 当前活跃文件是否开启日志功能 
        self.modified_files = set()  # 记录已加载文件修改状态

    # 加载txt文件到工作区
    def load_file(self, filepath: str):
        editor = TextEditor(filepath)
        filename = os.path.basename(filepath)
        self.editors[filename] = editor
        self.active_file = filename
        self.notify_observers(f"load {filename}")

    # 保存指定文件(未指定则保存当前活跃文件)
    def save_file(self, filename: str = None):
        filename = filename or self.active_file
        if filename in self.editors:
            editor = self.editors[filename]
            editor.save()
            self.modified_files.discard(filename)
            self.notify_observers(f"save {filename}")
        else:
            if filename == "all":
                for fname, editor in self.editors.items():
                    editor.save()
                    self.modified_files.discard(fname)
                    self.notify_observers(f"save {fname}")
            else:
                print(f"文件 {filename} 未打开，无法保存")

    def init_file(self, filename: str, with_logging: bool = False):
        if filename in self.editors:
            print(f"文件 {filename} 已存在，无法初始化")
            return
        filepath = os.path.join("data", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if with_logging:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# log\n")
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("")
        editor = TextEditor(filepath)
        self.editors[filename] = editor
        self.active_file = filename
        editor.modified = True
        self.modified_files.add(filename)
        self.notify_observers(f"init {filename}")

    # 关闭指定文件(未指定则关闭当前活跃文件)
    def close_file(self, filename: str = None):
        filename = filename or self.active_file
        if filename in self.editors:
            del self.editors[filename]
            self.modified_files.discard(filename)
            self.notify_observers(f"close {filename}")
            if filename == self.active_file:
                self.active_file = None
        else:
            print(f"文件 {filename} 未打开，无法关闭")

    def edit_file(self, filename: str):
        if filename in self.editors:
            self.active_file = filename
            self.notify_observers(f"edit {filename}")
        else:
            print(f"文件 {filename} 未打开，无法编辑")

    # 创建工作区状态备忘录对象
    def create_memento(self) -> WorkspaceMemento:
        state = {
            "open_files": list(self.editors.keys()),
            "active_file": self.active_file,
            "modified": list(self.modified_files),
            "log_enabled": self.log_enabled
        }
        return WorkspaceMemento(state)

    # 从备忘录对象恢复工作区状态
    def restore_from_memento(self, memento: WorkspaceMemento):
        state = memento.get_state()
        # 只恢复简单可序列化的状态（不恢复 undo/redo）
        self.log_enabled = state.get("log_enabled", False)
        self.modified_files = set(state.get("modified", []))
        self.active_file = state.get("active_file", None)
        # 延迟加载文件内容：这里我们选择重新 load 文件（恢复打开的文件列表）
        for fname in state.get("open_files", []):
            self.load_file(fname)

    # 持久化工作区状态到文件
    def persist_state(self):
        memento = self.create_memento()
        save_json(STATE_PATH, memento.get_state())

    # 从文件加载工作区状态
    def load_state(self):
        raw = load_json(STATE_PATH)
        if raw:
            self.restore_from_memento(WorkspaceMemento(raw))