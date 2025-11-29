import sys
import os
import shlex
from core.workspace import Workspace
from core.logger import Logger
from core.statistics import Statistics
from core.commands import AppendCommand, InsertCommand, DeleteCommand, ReplaceCommand
from core.xml_commands import (
    InsertBeforeCommand,
    AppendChildCommand,
    EditIdCommand,
    EditTextCommand,
    DeleteElementCommand,
)
from utils.file_helper import print_dir_tree, print_file_helper
from core.spellcheck import SimpleSpellChecker, LanguageToolHTTPSpellChecker

def main():
    # 1. 系统初始化
    # 初始化工作区
    workspace = Workspace()
    # 初始化日志模块
    logger = Logger()
    stats = Statistics()
    mode = os.environ.get("LANGTOOL_HTTP", "0")
    speller = LanguageToolHTTPSpellChecker(force_offline=(mode != "1"))
    # 将日志模块作为观察者注册到工作区
    workspace.attach(logger)
    workspace.attach(stats)
    workspace.load_workspace_state()
    print("==========================================")
    print(" Welcome to Lab1 Text Editor")
    print(" Type 'help' for command list (optional)")
    print(" Type 'exit' to quit")
    print("==========================================")

    # 2. 交互循环
    while True:
        try:
            prompt_file = workspace.active_editor_name if workspace.active_editor_name else "No file"
            try:
                user_input = input(f"[{prompt_file}] >> ").strip()
            except EOFError:
                print("\nEOF encountered. Exiting...")
                if workspace.check_and_exit():
                    print("Bye!")
                    sys.exit(0)
                else:
                    break
            
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
            elif cmd == "spell-check":
                target = args[0] if args else workspace.active_editor_name
                if not target:
                    print("Error: No file specified.")
                    continue
                ed = workspace.editors.get(target)
                if not ed:
                    print("Error: File not open.")
                    continue
                if hasattr(ed, 'lines'):
                    findings = speller.check_text(ed.lines)
                    print("拼写检查结果:")
                    if not findings:
                        print("无明显拼写错误")
                    for line, col, wrong, right in findings:
                        print(f"第{line}行，第{col}列: \"{wrong}\" -> 建议: {right}")
                else:
                    texts = []
                    for elem_id, elem in ed.id_index.items():
                        if elem.text and elem.text.strip():
                            texts.append((elem_id, elem.text))
                    findings = speller.check_xml_texts(texts)
                    print("拼写检查结果:")
                    if not findings:
                        print("无明显拼写错误")
                    for elem_id, wrong, right in findings:
                        print(f"元素 {elem_id}: \"{wrong}\" -> 建议: {right}")

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
                        base = os.path.basename(target)
                        with open(f".{base}.log", "r", encoding="utf-8") as f:
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
                    # 统一 delete：文本(.txt) 用 <line:col> <len>；XML(.xml) 用 <elementId>
                    if hasattr(editor, 'lines') and len(args) >= 2 and ':' in args[0]:
                        try:
                            l_str, c_str = args[0].split(':')
                            line, col = int(l_str), int(c_str)
                            length = int(args[1])
                            if editor.execute_command(DeleteCommand(editor, line, col, length)):
                                workspace.notify("command", {"filename": editor.filename, "command_str": user_input})
                        except ValueError:
                            print("Error: format should be delete line:col len")
                    elif hasattr(editor, 'id_index') and len(args) >= 1:
                        if editor.execute_command(DeleteElementCommand(editor, args[0])):
                            workspace.notify("command", {"filename": editor.filename, "command_str": user_input})
                    else:
                        if hasattr(editor, 'lines'):
                            print("Usage: delete <line:col> <len>")
                        else:
                            print("Usage: delete <elementId>")

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
                    if not hasattr(editor, 'lines'):
                        print("Error: show only applies to .txt files")
                        continue
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

                elif cmd == "xml-tree":
                    if hasattr(editor, 'xml_tree_lines'):
                        for line in editor.xml_tree_lines():
                            print(line)
                    else:
                        print("Error: xml-tree only applies to .xml files")
                elif cmd == "insert-before":
                    # insert-before <tag> <newId> <targetId> ["text"]
                    if len(args) < 3:
                        print("Usage: insert-before <tag> <newId> <targetId> [\"text\"]")
                        continue
                    text = args[3] if len(args) >= 4 else None
                    if hasattr(editor, 'execute_command'):
                        if editor.execute_command(InsertBeforeCommand(editor, args[0], args[1], args[2], text)):
                            workspace.notify("command", {"filename": editor.filename, "command_str": user_input})
                elif cmd == "append-child":
                    if len(args) < 3:
                        print("Usage: append-child <tag> <newId> <parentId> [\"text\"]")
                        continue
                    text = args[3] if len(args) >= 4 else None
                    if hasattr(editor, 'execute_command'):
                        if editor.execute_command(AppendChildCommand(editor, args[0], args[1], args[2], text)):
                            workspace.notify("command", {"filename": editor.filename, "command_str": user_input})
                elif cmd == "edit-id":
                    if len(args) < 2:
                        print("Usage: edit-id <oldId> <newId>")
                        continue
                    if hasattr(editor, 'execute_command'):
                        if editor.execute_command(EditIdCommand(editor, args[0], args[1])):
                            workspace.notify("command", {"filename": editor.filename, "command_str": user_input})
                elif cmd == "edit-text":
                    if not args:
                        print("Usage: edit-text <elementId> [\"text\"]")
                        continue
                    new_text = args[1] if len(args) >= 2 else None
                    if hasattr(editor, 'execute_command'):
                        if editor.execute_command(EditTextCommand(editor, args[0], new_text)):
                            workspace.notify("command", {"filename": editor.filename, "command_str": user_input})
                elif cmd == "delete":
                    if hasattr(editor, 'lines'):
                        if len(args) < 2:
                            print("Usage: delete <line:col> <len>")
                            continue
                        try:
                            if ':' not in args[0]:
                                raise ValueError
                            l_str, c_str = args[0].split(':')
                            line, col = int(l_str), int(c_str)
                            length = int(args[1])
                            if editor.execute_command(DeleteCommand(editor, line, col, length)):
                                workspace.notify("command", {"filename": editor.filename, "command_str": user_input})
                        except ValueError:
                            print("Error: format should be delete line:col len")
                    elif hasattr(editor, 'id_index'):
                        if not args:
                            print("Usage: delete <elementId>")
                            continue
                        if editor.execute_command(DeleteElementCommand(editor, args[0])):
                            workspace.notify("command", {"filename": editor.filename, "command_str": user_input})
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
