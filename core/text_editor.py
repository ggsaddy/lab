'''文本编辑器类实现'''
from typing import List
# from core.commands import AppendCommand, InsertCommand, DeleteCommand, ReplaceCommand

class TextEditor:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lines: List[str] = []  # 文件内容按行存储
        self.modified = False  # 文件是否被修改标志
        self.undo_stack = []      # 命令历史（undo 栈）
        self.redo_stack = []      # 命令历史（redo 栈）
        self.load() # 创建对象时自动加载文件内容

    # 文件加载
    def load(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.lines = f.read().splitlines()
        except FileNotFoundError:
            self.lines = []
        self.modified = False

    # 文件保存
    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(self.lines))
        self.modified = False

    # 文件显示
    def show(self, start: int = 1, end: int = None):
        if end is None: # 用户未指定结束行号，自动显示到文件末尾
            end = len(self.lines)
        if start < 1 or end > len(self.lines) or start > end:
            print("指定的显示行号范围无效！")
            return
        for i in range(start-1, end):
            print(f"第{i+1}行: {self.lines[i]}")

    # 执行命令并记录到历史栈
    def execute_command(self, command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()

    # 撤销操作
    def undo(self):
        if not self.undo_stack:
            print("当前无可撤销操作")
            return
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)

    # 重做操作
    def redo(self):
        if not self.redo_stack:
            print("当前无可重做操作")
            return
        cmd = self.redo_stack.pop()
        cmd.execute()
        self.undo_stack.append(cmd)

    '''# 文件追加
    def append(self, text: str):
        self.lines.append(text)
        self.modified = True

    # 文件插入
    def insert(self, line_no: int, text: str):
        if line_no < 1 or line_no > len(self.lines) + 1:
            print("指定的插入行号超出范围！")
            return
        self.lines.insert(line_no - 1, text) # 在指定行之前插入
        self.modified = True

    # 文件删除
    def delete(self, line_no: int):
        if line_no < 1 or line_no > len(self.lines):
            print("指定的删除行号超出范围！")
            return
        del self.lines[line_no - 1]
        self.modified = True

    # 文件替换
    def replace(self, line_no: int, text: str):
        if line_no < 1 or line_no > len(self.lines):
            print("指定的替换行号超出范围！")
            return
        self.lines[line_no - 1] = text
        self.modified = True'''