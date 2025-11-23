"""工作区状态的备忘录模式实现"""
import json
import os
from typing import List, Dict, Optional

class WorkspaceMemento:
    """备忘录类 - 存储工作区状态的快照"""
    
    def __init__(self, active_editor: Optional[str], 
                 files_data: List[Dict], 
                 logged_files: List[str]):
        """
        Args:
            active_editor: 当前活动文件名
            files_data: 文件信息列表 [{"name": str, "modified": bool}, ...]
            logged_files: 开启日志的文件名列表
        """
        self._active_editor = active_editor
        self._files_data = files_data.copy()
        self._logged_files = logged_files.copy()
    
    def get_state(self) -> dict:
        """获取状态快照"""
        return {
            "active": self._active_editor,
            "files": self._files_data,
            "logged_files": self._logged_files
        }


class WorkspaceCaretaker:
    """管理者类 - 负责备忘录的持久化到磁盘"""
    
    def __init__(self, storage_file: str = ".workspace_state.json"):
        self.storage_file = storage_file
    
    def save(self, memento: WorkspaceMemento) -> bool:
        """保存备忘录到文件"""
        try:
            state = memento.get_state()
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving workspace state: {e}")
            return False
    
    def load(self) -> Optional[WorkspaceMemento]:
        """从文件加载备忘录"""
        if not os.path.exists(self.storage_file):
            return None
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # 兼容旧版本格式
            files_data = state.get("files", [])
            if files_data and isinstance(files_data[0], str):
                # 旧格式：只有文件名列表
                files_data = [{"name": fname, "modified": False} for fname in files_data]
            
            logged_files = state.get("logged_files", [])
            
            return WorkspaceMemento(
                active_editor=state.get("active"),
                files_data=files_data,
                logged_files=logged_files
            )
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load workspace state: {e}")
            return None