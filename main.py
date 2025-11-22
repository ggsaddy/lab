import sys
import shlex
from core.workspace import Workspace
from core.logger import Logger
from core.commands import AppendCommand, InsertCommand, DeleteCommand, ReplaceCommand
from utils.file_helper import print_dir_tree, print_file_helper

def main():
    # 1. 系统初始化
    # 初始化工作区
    workspace = Workspace()
    # 初始化日志模块
    logger = Logger()
    # 将日志模块作为观察者注册到工作区
    workspace.attach(logger) 
    
    print("==========================================")
    print(" Welcome to Lab1 Text Editor")
    print(" Type 'help' for command list (optional)")
    print(" Type 'exit' to quit")
    print("==========================================")

    # 2. 交互循环
    while True:
        try:
            # 获取输入前缀，提示当前文件
            prompt_file = workspace.active_editor_name if workspace.active_editor_name else "No file"
            user_input = input(f"[{prompt_file}] >> ").strip()
            
            if not user_input:
                continue

            # 解析命令 (处理带引号的参数)
            try:
                parts = shlex.split(user_input)
            except ValueError:
                print("Error: Invalid command format (unmatched quotes).")
                continue

            if not parts:
                continue

            cmd = parts[0]
            args = parts[1:]

            # ==============================
            # 指令说明命令
            # ==============================
            if cmd == "help":
                print_file_helper()
                continue

            # ==============================
            # 全局/工作区命令
            # ==============================
            if cmd == "exit":
                # 【修改点】调用 check_and_exit 处理未保存文件的交互逻辑
                # 如果返回 True，说明用户处理完了所有文件（保存或放弃），可以安全退出
                if workspace.check_and_exit():
                    print("Bye!")
                    sys.exit(0)
            
            elif cmd == "load":
                if not args: print("Usage: load <file>"); continue
                workspace.load_file(args[0])

            elif cmd == "save":
                target = args[0] if args else None
                workspace.save_file(target)

            elif cmd == "init":
                if not args: print("Usage: init <file> [with-log]"); continue
                with_log = "with-log" in args
                workspace.init_file(args[0], with_log)

            elif cmd == "close":
                target = args[0] if args else None
                workspace.close_file(target)
            
            elif cmd == "edit":
                if not args: print("Usage: edit <file>"); continue
                workspace.switch_editor(args[0])

            elif cmd == "editor-list":
                workspace.list_editors()

            elif cmd == "dir-tree":
                path = args[0] if args else "."
                print_dir_tree(path)

            # ==============================
            # 日志命令
            # ==============================
            elif cmd == "log-on":
                target = args[0] if args else workspace.active_editor_name
                if target: workspace.notify("log_on", {"filename": target})
                else: print("Error: No file specified.")

            elif cmd == "log-off":
                target = args[0] if args else workspace.active_editor_name
                if target: workspace.notify("log_off", {"filename": target})

            elif cmd == "log-show":
                target = args[0] if args else workspace.active_editor_name
                if target:
                    try:
                        # 尝试读取隐藏的日志文件
                        with open(f".{target}.log", "r", encoding="utf-8") as f:
                            print(f"--- Log for {target} ---")
                            print(f.read())
                            print("------------------------")
                    except FileNotFoundError:
                        print("No log file found.")
                else: print("Error: No file specified.")

            # ==============================
            # 编辑器命令 (需要有活动文件)
            # ==============================
            elif workspace.active_editor:
                editor = workspace.active_editor
                
                if cmd == "append":
                    if not args: print("Usage: append \"text\""); continue
                    if editor.execute_command(AppendCommand(editor, args[0])):
                        workspace.notify("command", {"filename": editor.filename, "command_str": user_input})

                elif cmd == "insert":
                    # insert line:col "text"
                    if len(args) < 2: print("Usage: insert <line:col> \"text\""); continue
                    try:
                        if ':' not in args[0]: raise ValueError
                        l_str, c_str = args[0].split(':')
                        line, col = int(l_str), int(c_str)
                        if editor.execute_command(InsertCommand(editor, line, col, args[1])):
                            workspace.notify("command", {"filename": editor.filename, "command_str": user_input})
                    except ValueError:
                        print("Error: format should be insert line:col \"text\"")

                elif cmd == "delete":
                    # delete line:col len
                    if len(args) < 2: print("Usage: delete <line:col> <len>"); continue
                    try:
                        if ':' not in args[0]: raise ValueError
                        l_str, c_str = args[0].split(':')
                        line, col = int(l_str), int(c_str)
                        length = int(args[1])
                        if editor.execute_command(DeleteCommand(editor, line, col, length)):
                            workspace.notify("command", {"filename": editor.filename, "command_str": user_input})
                    except ValueError:
                        print("Error: format should be delete line:col len")

                elif cmd == "replace":
                    # replace line:col len "text"
                    if len(args) < 3: print("Usage: replace <line:col> <len> \"text\""); continue
                    try:
                        if ':' not in args[0]: raise ValueError
                        l_str, c_str = args[0].split(':')
                        line, col = int(l_str), int(c_str)
                        length = int(args[1])
                        if editor.execute_command(ReplaceCommand(editor, line, col, length, args[2])):
                            workspace.notify("command", {"filename": editor.filename, "command_str": user_input})
                    except ValueError:
                        print("Error: format should be replace line:col len \"text\"")

                elif cmd == "undo":
                    editor.undo()
                    workspace.notify("command", {"filename": editor.filename, "command_str": "undo"})
                    print("Undone.")

                elif cmd == "redo":
                    editor.redo()
                    workspace.notify("command", {"filename": editor.filename, "command_str": "redo"})
                    print("Redone.")

                elif cmd == "show":
                    # show [start:end]
                    start, end = 1, -1
                    if args:
                        try:
                            if ':' in args[0]:
                                s, e = args[0].split(':')
                                start = int(s) if s else 1
                                end = int(e) if e else -1
                        except ValueError: 
                            print("Error: format should be show start:end")
                            continue
                    
                    lines = editor.lines
                    total = len(lines)
                    s_idx = max(0, start - 1)
                    e_idx = total if end == -1 else min(total, end)
                    
                    for i in range(s_idx, e_idx):
                        print(f"{i+1}: {lines[i]}")

                else:
                    print(f"Unknown command: {cmd}")
            
            else:
                # 没有活动文件时的提示
                print(f"Unknown command '{cmd}' or no active file open.")

        except KeyboardInterrupt:
            # 捕获 Ctrl+C，同样走安全退出流程
            print("\nExiting...")
            if workspace.check_and_exit():
                sys.exit(0)
            else:
                continue # 如果用户在 check_and_exit 中取消了退出（虽然目前的逻辑没这个选项，但保留扩展性）
        except Exception as e:
            print(f"System Error: {e}")

if __name__ == "__main__":
    main()
