'''观察者模式实现'''

class Observer: # 定义观察者接口
    def update(self, subject):
        '''当被观察者状态改变时继承的观察者子类调用此方法'''
        raise NotImplementedError
    
class Subject: # 管理观察者列表并广播消息
    def __init__(self):
        self._observers = []

    def attach(self, obs: Observer):
        if obs not in self._observers:
            '''添加观察者对象'''
            self._observers.append(obs)

    def detach(self, obs: Observer):
        if obs in self._observers:
            '''移除观察者对象'''
            self._observers.remove(obs)

    def notify_observers(self, message: str):
        for obs in list(self._observers):
            try:
                obs.update(message)
            except Exception as e:
                '''观察者异常不应影响主流程'''
                print(f"Warning: observer error: {e}")