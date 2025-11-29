from typing import List, Optional, Dict
import xml.etree.ElementTree as ET

class XmlEditor:
    def __init__(self, filename: str, xml_text: Optional[str] = None, log_config_line: Optional[str] = None):
        self.filename = filename
        self.is_modified = False
        self._undo_stack: List[object] = []
        self._redo_stack: List[object] = []
        self.log_config_line = log_config_line
        if xml_text:
            self.root = ET.fromstring(xml_text)
        else:
            self.root = ET.Element("root")
            self.root.set("id", "root")
        self.id_index: Dict[str, ET.Element] = {}
        self._rebuild_index()

    def _rebuild_index(self):
        self.id_index.clear()
        def walk(e: ET.Element):
            if "id" in e.attrib:
                self.id_index[e.attrib["id"]] = e
            for c in list(e):
                walk(c)
        walk(self.root)

    def execute_command(self, command) -> bool:
        if command.execute():
            self._undo_stack.append(command)
            self._redo_stack.clear()
            self.is_modified = True
            return True
        return False

    def undo(self):
        if self._undo_stack:
            cmd = self._undo_stack.pop()
            cmd.undo()
            self._redo_stack.append(cmd)
            self.is_modified = True

    def redo(self):
        if self._redo_stack:
            cmd = self._redo_stack.pop()
            if cmd.execute():
                self._undo_stack.append(cmd)
                self.is_modified = True

    def get_content_str(self) -> str:
        xml_str = ET.tostring(self.root, encoding="unicode")
        decl = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        prefix = self.log_config_line + "\n" if self.log_config_line else ""
        return prefix + decl + xml_str

    def find_parent(self, target: ET.Element) -> Optional[ET.Element]:
        parent = None
        def walk(e: ET.Element):
            nonlocal parent
            for c in list(e):
                if c is target:
                    parent = e
                    return True
                if walk(c):
                    return True
            return False
        walk(self.root)
        return parent

    def xml_tree_lines(self) -> List[str]:
        lines: List[str] = []
        def attrs_str(e: ET.Element) -> str:
            parts = []
            for k, v in e.attrib.items():
                parts.append(f"{k}=\"{v}\"")
            if parts:
                return " [" + ", ".join(parts) + "]"
            return ""
        def walk_children(e: ET.Element, prefix: str):
            children = list(e)
            n = len(children)
            for i, c in enumerate(children):
                is_last = i == n - 1
                conn = "└── " if is_last else "├── "
                lines.append(prefix + conn + c.tag + attrs_str(c))
                ext = "    " if is_last else "│   "
                if c.text and c.text.strip():
                    lines.append(prefix + ext + "└── " + "\"" + c.text.strip() + "\"")
                walk_children(c, prefix + ext)
        lines.append(self.root.tag + attrs_str(self.root))
        if self.root.text and self.root.text.strip():
            lines.append("└── " + "\"" + self.root.text.strip() + "\"")
        walk_children(self.root, "")
        return lines
