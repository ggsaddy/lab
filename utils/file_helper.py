import os
import xml.etree.ElementTree as ET
from core.tree_view import ConsoleTreeView, FileSystemTreeDataProvider, XmlTreeDataProvider

def print_dir_tree(startpath: str):
    """
    打印目录树结构
    类似于 Linux 的 tree 命令
    """
    provider = FileSystemTreeDataProvider(startpath)
    view = ConsoleTreeView(provider)
    view.show()

def print_xml_tree(root_element: ET.Element):
    """
    打印 XML 树结构
    """
    provider = XmlTreeDataProvider(root_element)
    view = ConsoleTreeView(provider)
    view.show()


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
