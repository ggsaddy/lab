from abc import ABC, abstractmethod
from typing import List, Any, Optional
import os
import xml.etree.ElementTree as ET

class TreeItem:
    def __init__(self, label: str, collapsible_state: int = 0):
        self.label = label
        # collapsible_state: 0 = None (Leaf), 1 = Collapsed (Node)
        # In this simplified console version, we just treat anything with children as a Node.
        self.collapsible_state = collapsible_state

class TreeDataProvider(ABC):
    """
    A data provider that supplies data for a tree view.
    Modeled after VS Code's TreeDataProvider.
    """
    @abstractmethod
    def get_children(self, element: Optional[Any] = None) -> List[Any]:
        """
        Get the children of `element` or root if `element` is None.
        """
        pass

    @abstractmethod
    def get_tree_item(self, element: Any) -> TreeItem:
        """
        Get the TreeItem representation of `element`.
        """
        pass

class ConsoleTreeView:
    """
    A simplified Tree View that prints to the console.
    """
    def __init__(self, tree_data_provider: TreeDataProvider):
        self.provider = tree_data_provider

    def show(self):
        roots = self.provider.get_children(None)
        if not roots:
            return
        for i, root in enumerate(roots):   
            self._print_node(root, "", is_last=(i == len(roots) - 1), is_root=True)

    def _print_node(self, element: Any, prefix: str, is_last: bool, is_root: bool = False):
        item = self.provider.get_tree_item(element)
        
        if is_root:
            print(item.label)
            new_prefix = ""
        else:
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{item.label}")
            new_prefix = prefix + ("    " if is_last else "│   ")
        
        children = self.provider.get_children(element)
        for i, child in enumerate(children):
            self._print_node(child, new_prefix, i == len(children) - 1)

class FileSystemTreeDataProvider(TreeDataProvider):
    def __init__(self, root_path: str):
        self.root_path = root_path

    def get_children(self, element: Optional[Any] = None) -> List[Any]:
        if element is None:
            return [self.root_path]
        
        path = element
        if os.path.isdir(path):
            try:
                entries = [e for e in os.listdir(path) if not e.startswith('.')]
                entries.sort()
                return [os.path.join(path, e) for e in entries]
            except OSError:
                return []
        return []

    def get_tree_item(self, element: Any) -> TreeItem:
        path = element
        label = os.path.basename(os.path.abspath(path))
        if os.path.isdir(path):
            label += "/"
        return TreeItem(label)

class XmlTreeDataProvider(TreeDataProvider):
    def __init__(self, root_element: ET.Element):
        self.root_element = root_element

    def get_children(self, element: Optional[Any] = None) -> List[Any]:
        if element is None:
            return [self.root_element]
        
        if isinstance(element, ET.Element):
            children = []
            # Add text content as first child if exists
            if element.text and element.text.strip():
                children.append(f"TEXT:{element.text.strip()}")
            
            # Add sub-elements
            children.extend(list(element))
            return children
        
        return []

    def get_tree_item(self, element: Any) -> TreeItem:
        if isinstance(element, ET.Element):
            label = element.tag
            parts = []
            for k, v in element.attrib.items():
                parts.append(f"{k}=\"{v}\"")
            if parts:
                label += " [" + ", ".join(parts) + "]"
            return TreeItem(label)
        elif isinstance(element, str) and element.startswith("TEXT:"):
            return TreeItem(f"\"{element[5:]}\"")
        return TreeItem(str(element))


