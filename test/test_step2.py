import sys
sys.path.append("..")
from core.editor import TextEditor
from core.commands import AppendCommand, InsertCommand, DeleteCommand, ReplaceCommand

def print_editor_state(editor, step_name):
    print(f"--- {step_name} ---")
    # 模拟简单的 show 命令
    for i, line in enumerate(editor.lines):
        print(f"{i+1}: {line}")
    print(f"Is Modified: {editor.is_modified}")
    print("----------------\n")

def main():
    # 1. 初始化编辑器
    print(">>> 初始化编辑器...")
    editor = TextEditor("test.txt")
    
    # 2. 测试 Append
    cmd1 = AppendCommand(editor, "Hello World")
    editor.execute_command(cmd1)
    print_editor_state(editor, "执行 Append 'Hello World'")

    # 3. 测试 Append 第二行
    cmd2 = AppendCommand(editor, "This is line 2")
    editor.execute_command(cmd2)
    print_editor_state(editor, "执行 Append 'This is line 2'")

    # 4. 测试 Insert (在第1行第6列插入 " Python")
    # 预期: "Hello World" -> "Hello Python World"
    cmd3 = InsertCommand(editor, 1, 6, " Python")
    editor.execute_command(cmd3)
    print_editor_state(editor, "执行 Insert 1:6 ' Python'")

    # 5. 测试 Undo (撤销 Insert)
    editor.undo()
    print_editor_state(editor, "撤销 Insert (回到 Hello World)")

    # 6. 测试 Redo (重做 Insert)
    editor.redo()
    print_editor_state(editor, "重做 Insert (回到 Hello Python World)")

    # 7. 测试 Delete (删除第1行 ' Python' 这7个字符)
    # 当前: "Hello Python World" (注意: 索引从0开始，'P'在索引5)
    # Insert时是在第6列插入(索引5)，现在要把这部分删掉还原
    # delete 1:6 7
    cmd4 = DeleteCommand(editor, 1, 6, 7)
    editor.execute_command(cmd4)
    print_editor_state(editor, "执行 Delete 1:6 7 (删除 ' Python')")

    # 8. 测试 Replace (把第2行 'line' 替换为 'Code')
    # 当前第2行: "This is line 2"
    # 'line' 起始位置: 索引8 (第9列)
    cmd5 = ReplaceCommand(editor, 2, 9, 4, "Code")
    editor.execute_command(cmd5)
    print_editor_state(editor, "执行 Replace 2:9 4 'Code'")
    
    # 9. 连续撤销测试
    editor.undo() # 撤销 Replace
    editor.undo() # 撤销 Delete
    print_editor_state(editor, "连续撤销两次 (应回到含 ' Python' 的状态)")

if __name__ == "__main__":
    main()
