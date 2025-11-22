from abc import ABC, abstractmethod

# === Command Pattern ===
class Command(ABC):
    """base command interface"""
    @abstractmethod
    def execute(self) -> bool:
        pass

    @abstractmethod
    def undo(self):
        pass

# === Observer Pattern ===
class Observer(ABC):
    """base observer interface"""
    @abstractmethod
    def update(self, event_type: str, data: dict):
        pass

class Subject:
    """base subject interface"""
    def __init__(self):
        self._observers = []

    def attach(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer):
        self._observers.remove(observer)

    def notify(self, event_type: str, data: dict):
        for observer in self._observers:
            observer.update(event_type, data)
