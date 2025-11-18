'''命令模式实现'''
from abc import ABC, abstractmethod

class Command(ABC):
    """命令基类，所有命令都要继承它"""

    @abstractmethod
    def execute(self):
        """执行命令"""
        pass

    @abstractmethod
    def undo(self):
        """撤销命令"""
        pass

class AppendCommand(Command):
    def __init__(self, editor, text: str):
        self.editor = editor
        self.text = text

    def execute(self):
        self.editor.lines.append(self.text)
        self.editor.modified = True

    def undo(self):
        # 撤销 append 就是删除最后一行
        if self.editor.lines:
            self.editor.lines.pop()
            self.editor.modified = True

class InsertCommand(Command):
    def __init__(self, editor, line_no: int, text: str):
        self.editor = editor
        self.line_no = line_no
        self.text = text

    def execute(self):
        self.editor.insert(self.line_no, self.text)

    def undo(self):
        self.editor.delete(self.line_no)

class DeleteCommand(Command):
    def __init__(self, editor, line_no: int, line_col: int, len: int):
        self.editor = editor
        self.line_no = line_no
        self.line_col = line_col
        self.len = len
        self.deleted_line = None

    def execute(self):
        # 先保存被删除的内容
        if 1 <= self.line_no <= len(self.editor.lines):
            self.deleted_line = self.editor.lines[self.line_no - 1]
        self.editor.delete(self.line_no)

    def undo(self):
        if self.deleted_line is not None:
            self.editor.insert(self.line_no, self.deleted_line)

class ReplaceCommand(Command):
    def __init__(self, editor, line_no: int, line_col: int, len: int, new_text: str):
        self.editor = editor
        self.line_no = line_no
        self.line_col = line_col
        self.len = len
        self.new_text = new_text
        self.old_text = None

    def execute(self):
        if 1 <= self.line_no <= len(self.editor.lines):
            self.old_text = self.editor.lines[self.line_no - 1]
        self.editor.replace(self.line_no, self.new_text)

    def undo(self):
        if self.old_text is not None:
            self.editor.replace(self.line_no, self.old_text)

