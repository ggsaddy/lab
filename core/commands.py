from typing import TYPE_CHECKING
from .interfaces import Command

# 使用 TYPE_CHECKING 避免运行时循环导入
if TYPE_CHECKING:
    from .editor import TextEditor

class AppendCommand(Command):
    """
    功能: 在文件末尾追加一行文本
    命令: append "text"
    """
    def __init__(self, editor: 'TextEditor', text: str):
        self.editor = editor
        self.text = text
        self.added_index = -1  # 用于记录追加在哪一行

    def execute(self) -> bool:
        self.editor.lines.append(self.text)
        self.added_index = len(self.editor.lines) - 1
        return True

    def undo(self):
        # 只有当确实追加了行才执行删除
        if self.added_index != -1 and self.added_index < len(self.editor.lines):
            self.editor.lines.pop(self.added_index)

class InsertCommand(Command):
    """
    功能: 在指定行号和列号插入文本
    命令: insert <line:col> "text"
    """
    def __init__(self, editor: 'TextEditor', line: int, col: int, text: str):
        self.editor = editor
        self.line_idx = line - 1  # 转为 0-based
        self.col_idx = col - 1    # 转为 0-based
        self.text = text
        self.old_line_content = None # 备份修改前的行内容

    def execute(self) -> bool:
        # 1. 边界检查
        if not (0 <= self.line_idx < len(self.editor.lines)):
            print(f"Error: Line number {self.line_idx + 1} out of range.")
            return False
        
        current_line = self.editor.lines[self.line_idx]
        
        # 2. 列越界检查 (允许插在行尾，即 col_idx == len)
        if self.col_idx < 0 or self.col_idx > len(current_line):
            print(f"Error: Column number {self.col_idx + 1} out of range.")
            return False

        # 3. 备份并执行插入
        self.old_line_content = current_line
        
        # 简单的字符串切片插入
        new_line = current_line[:self.col_idx] + self.text + current_line[self.col_idx:]
        self.editor.lines[self.line_idx] = new_line
        return True

    def undo(self):
        if self.old_line_content is not None:
            self.editor.lines[self.line_idx] = self.old_line_content

class DeleteCommand(Command):
    """
    功能: 删除指定位置开始的 len 个字符
    命令: delete <line:col> <len>
    """
    def __init__(self, editor: 'TextEditor', line: int, col: int, length: int):
        self.editor = editor
        self.line_idx = line - 1
        self.col_idx = col - 1
        self.length = length
        self.old_line_content = None

    def execute(self) -> bool:
        if not (0 <= self.line_idx < len(self.editor.lines)):
            print("Error: Line number out of range.")
            return False
            
        current_line = self.editor.lines[self.line_idx]
        
        if self.col_idx < 0 or self.col_idx >= len(current_line):
            print("Error: Column start position out of range.")
            return False

        # 检查删除长度是否超出该行
        if self.col_idx + self.length > len(current_line):
            print("Error: Delete length exceeds line end.")
            return False

        # 备份并执行删除
        self.old_line_content = current_line
        new_line = current_line[:self.col_idx] + current_line[self.col_idx + self.length:]
        self.editor.lines[self.line_idx] = new_line
        return True

    def undo(self):
        if self.old_line_content is not None:
            self.editor.lines[self.line_idx] = self.old_line_content

class ReplaceCommand(Command):
    """
    功能: 替换指定位置的文本 (相当于 Delete + Insert)
    命令: replace <line:col> <len> "text"
    """
    def __init__(self, editor: 'TextEditor', line: int, col: int, length: int, text: str):
        self.editor = editor
        self.line_idx = line - 1
        self.col_idx = col - 1
        self.length = length
        self.text = text
        self.old_line_content = None

    def execute(self) -> bool:
        if not (0 <= self.line_idx < len(self.editor.lines)):
            print("Error: Line number out of range.")
            return False
            
        current_line = self.editor.lines[self.line_idx]
        
        # 检查范围
        if self.col_idx < 0 or self.col_idx + self.length > len(current_line):
            print("Error: Replace range out of bounds.")
            return False

        # 备份并执行替换
        self.old_line_content = current_line
        # 先删掉中间一段，再拼接新文本
        prefix = current_line[:self.col_idx]
        suffix = current_line[self.col_idx + self.length:]
        new_line = prefix + self.text + suffix
        
        self.editor.lines[self.line_idx] = new_line
        return True

    def undo(self):
        if self.old_line_content is not None:
            self.editor.lines[self.line_idx] = self.old_line_content
