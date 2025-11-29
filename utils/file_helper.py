import os

def print_dir_tree(startpath: str):
    """
    打印目录树结构
    类似于 Linux 的 tree 命令
    """
    print(f"{os.path.basename(os.path.abspath(startpath))}/")
    
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = '│   ' * (level)
        
        # 为了美观，过滤掉隐藏文件夹（可选）
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        subindent = '│   ' * (level + 1)
        
        # 打印当前目录下的文件
        for i, f in enumerate(files):
            # 跳过隐藏文件和日志文件（可选，根据需求）
            if f.startswith('.'):
                continue
                
            # 判断是不是最后一个文件，用于决定使用 └── 还是 ├──
            is_last = (i == len(files) - 1) and not dirs
            prefix = '└── ' if is_last else '├── '
            
            # 如果是在根目录下，直接用 indent；如果是子目录，用 subindent
            # 这里简化处理，直接打印相对层级
            # 注意：os.walk 的顺序可能导致树形画线稍微复杂，
            # 为了最简单实现 Lab 要求，我们采用一种递归打印的方法可能更直观，
            # 但 os.walk 更稳健。下面是一个简化的显示逻辑：
            pass 

    # --- 为了更精确控制树形符号，改用递归实现 ---
    _print_tree_recursive(startpath, "")

def _print_tree_recursive(path: str, prefix: str):
    try:
        # 获取目录下所有条目并排序
        entries = [e for e in os.listdir(path) if not e.startswith('.')]
        entries.sort()
    except OSError:
        return

    total = len(entries)
    for i, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        is_last = (i == total - 1)
        
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{entry}")
        
        if os.path.isdir(full_path):
            extension = "    " if is_last else "│   "
            _print_tree_recursive(full_path, prefix + extension)

def print_file_helper():
    """
    打印文件帮助信息
    """
    help_text = """
Available commands:

  Workspace:
    load <file>                         - Load file into workspace (.txt/.xml)
    save [file|all]                     - Save current file or all files
    init <file> [with-log]              - Create new buffer (type by extension)
    close [file]                        - Close current or specified file
    edit <file>                         - Switch active file
    editor-list                         - List all loaded files (show duration)
    dir-tree [path]                     - Display directory tree
    undo                                - Undo last action
    redo                                - Redo last undone action
    exit                                - Exit the program

  Text Editing (only for .txt files):
    append "text"                       - Append text to the end of file
    insert <line:col> "text"            - Insert text at specified position
    delete <line:col> <len>             - Delete characters starting from position
    replace <line:col> <len> "text"     - Replace characters with provided text
    show [start:end]                    - Show full or partial file content

  XML Editing (only for .xml files):
    xml-tree                            - Show XML tree
    insert-before <tag> <newId> <targetId> ["text"]
    append-child   <tag> <newId> <parentId> ["text"]
    edit-id        <oldId> <newId>
    edit-text      <elementId> ["text"]
    delete         <elementId>

  Logging:
    log-on [file]                       - Enable logging (optionally for specific file)
    log-off [file]                      - Disable logging
    log-show [file]                     - Display log for file

  Tips: [] indicates optional parameters, while <> indicates required parameters.
"""
    print(help_text.strip())
