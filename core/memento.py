'''备忘录模式实现'''

class WorkspaceMemento:
    def __init__(self, state: dict):
        '''保存工作区状态'''
        self._state = state

    def get_state(self) -> dict:
        '''获取工作区状态'''
        return self._state