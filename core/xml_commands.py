from typing import Optional
import xml.etree.ElementTree as ET

class InsertBeforeCommand:
    def __init__(self, editor, tag: str, new_id: str, target_id: str, text: Optional[str] = None):
        self.editor = editor
        self.tag = tag
        self.new_id = new_id
        self.target_id = target_id
        self.text = text
        self.created = None
        self.parent = None
        self.index = None

    def execute(self) -> bool:
        if self.new_id in self.editor.id_index:
            print(f"元素ID已存在: {self.new_id}")
            return False
        target = self.editor.id_index.get(self.target_id)
        if target is None:
            print(f"目标元素不存在: {self.target_id}")
            return False
        parent = self.editor.find_parent(target)
        if parent is None:
            print("不能在根元素前插入元素")
            return False
        elem = ET.Element(self.tag)
        elem.set("id", self.new_id)
        if self.text is not None:
            elem.text = self.text
        children = list(parent)
        idx = children.index(target)
        parent.insert(idx, elem)
        self.created = elem
        self.parent = parent
        self.index = idx
        self.editor._rebuild_index()
        return True

    def undo(self):
        if self.parent is not None and self.created is not None:
            self.parent.remove(self.created)
            self.editor._rebuild_index()

class AppendChildCommand:
    def __init__(self, editor, tag: str, new_id: str, parent_id: str, text: Optional[str] = None):
        self.editor = editor
        self.tag = tag
        self.new_id = new_id
        self.parent_id = parent_id
        self.text = text
        self.created = None
        self.parent = None

    def execute(self) -> bool:
        if self.new_id in self.editor.id_index:
            print(f"元素ID已存在: {self.new_id}")
            return False
        parent = self.editor.id_index.get(self.parent_id)
        if parent is None:
            print(f"父元素不存在: {self.parent_id}")
            return False
        elem = ET.Element(self.tag)
        elem.set("id", self.new_id)
        if self.text is not None:
            elem.text = self.text
        parent.append(elem)
        self.created = elem
        self.parent = parent
        self.editor._rebuild_index()
        return True

    def undo(self):
        if self.parent is not None and self.created is not None:
            self.parent.remove(self.created)
            self.editor._rebuild_index()

class EditIdCommand:
    def __init__(self, editor, old_id: str, new_id: str):
        self.editor = editor
        self.old_id = old_id
        self.new_id = new_id
        self.target = None

    def execute(self) -> bool:
        if self.old_id not in self.editor.id_index:
            print(f"元素不存在: {self.old_id}")
            return False
        if self.new_id in self.editor.id_index:
            print(f"目标ID已存在: {self.new_id}")
            return False
        elem = self.editor.id_index[self.old_id]
        if elem is self.editor.root:
            print("不建议修改根元素ID")
            return False
        elem.set("id", self.new_id)
        self.target = elem
        self.editor._rebuild_index()
        return True

    def undo(self):
        if self.target is not None:
            self.target.set("id", self.old_id)
            self.editor._rebuild_index()

class EditTextCommand:
    def __init__(self, editor, element_id: str, text: Optional[str]):
        self.editor = editor
        self.element_id = element_id
        self.text = text
        self.target = None
        self.prev = None

    def execute(self) -> bool:
        target = self.editor.id_index.get(self.element_id)
        if target is None:
            print(f"元素不存在: {self.element_id}")
            return False
        self.prev = target.text
        target.text = self.text if self.text is not None else None
        self.target = target
        return True

    def undo(self):
        if self.target is not None:
            self.target.text = self.prev

class DeleteElementCommand:
    def __init__(self, editor, element_id: str):
        self.editor = editor
        self.element_id = element_id
        self.target = None
        self.parent = None
        self.index = None

    def execute(self) -> bool:
        target = self.editor.id_index.get(self.element_id)
        if target is None:
            print(f"元素不存在: {self.element_id}")
            return False
        if target is self.editor.root:
            print("不能删除根元素")
            return False
        parent = self.editor.find_parent(target)
        children = list(parent)
        idx = children.index(target)
        parent.remove(target)
        self.target = target
        self.parent = parent
        self.index = idx
        self.editor._rebuild_index()
        return True

    def undo(self):
        if self.parent is not None and self.target is not None and self.index is not None:
            self.parent.insert(self.index, self.target)
            self.editor._rebuild_index()

