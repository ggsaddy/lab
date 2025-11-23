from typing import List
from .interfaces import Command

class TextEditor:
    def __init__(self, filename: str, content: List[str] = None):
        self.filename = filename
        self.lines: List[str] = content if content is not None else []
        self.is_modified = False
        
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []

    def get_content_str(self) -> str:
        """获取用于保存的完整文本内容"""
        return "\n".join(self.lines)

    def execute_command(self, command: Command) -> bool:
        """执行命令并压入撤销栈"""
        if command.execute():
            self._undo_stack.append(command)
            self._redo_stack.clear()  # 新操作会清空重做栈
            # self.is_modified = True
            return True
        return False

    def undo(self):
        """执行撤销"""
        if self._undo_stack:
            cmd = self._undo_stack.pop()
            cmd.undo()
            self._redo_stack.append(cmd)
            # 注意：简单的 undo 后通常认为文件仍是被修改过的，
            # 除非我们实现更复杂的 hash 对比，这里暂定为 True
            # self.is_modified = True

    def redo(self):
        """执行重做"""
        if self._redo_stack:
            cmd = self._redo_stack.pop()
            if cmd.execute():
                self._undo_stack.append(cmd)
                # self.is_modified = True
    # --- 辅助方法：处理显示范围 ---
    def get_lines_view(self, start: int = 1, end: int = -1):
        """获取指定范围的行（带行号），start从1开始"""
        total_lines = len(self.lines)
        if total_lines == 0:
            return []
            
        start_idx = max(0, start - 1)
        if end == -1 or end > total_lines:
            end_idx = total_lines
        else:
            end_idx = end
            
        result = []
        for i in range(start_idx, end_idx):
            result.append(f"{i + 1}: {self.lines[i]}")
        return result
    
"""装饰器基类，保持与 TextEditor 相同接口"""
class EditorDecorator:
    def __init__(self, editor: TextEditor):
        self._editor = editor

    # 代理属性访问
    def __getattr__(self, name):
        return getattr(self._editor, name)
        
class AutoModifiedDecorator(EditorDecorator):
    """在执行任何命令后自动标记文件为已修改"""

    def execute_command(self, command) -> bool:
        result = self._editor.execute_command(command)
        if result:
            self._editor.is_modified = True
        return result

    def undo(self):
        self._editor.undo()
        self._editor.is_modified = True

    def redo(self):
        self._editor.redo()
        self._editor.is_modified = True
