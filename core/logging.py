'''日志记录模块'''
import os
from datetime import datetime
from core.observer import Observer


class Logger(Observer):
    def __init__(self):
        self.enabled = False  # 日志启用开关
        self.log_file = None  # 日志文件路径
        self.session_started = False

    def start_session(self, filepath: str):
        """开始新会话并设置日志文件"""
        log_name = f".{os.path.basename(filepath)}.log"
        self.log_file = f"./logging/{log_name}"
        self.session_started = True
        self._write_line(f"session start at {self._timestamp()}")

    def _timestamp(self):
        return datetime.now().strftime("%Y%m%d %H:%M:%S")

    # 写入日志行，若不存在日志文件则自动生成
    def _write_line(self, text: str):
        if not self.enabled or not self.log_file:
            return
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception as e:
            print(f"日志写入失败: {e}")

    def update(self, event: str, data: dict = None):
        """响应被观察对象的通知"""
        if not self.enabled:
            return
        if not self.session_started and data and "filename" in data:
            self.start_session(data["filename"])
        cmd_str = f"{self._timestamp()} {event}"
        if data and "args" in data:
            cmd_str += f" {data['args']}"
        self._write_line(cmd_str)

    # 手动控制日志开关
    def enable(self):
        self.enabled = True
        print("日志已开启")

    def disable(self):
        self.enabled = False
        print("日志已关闭")

    def show(self):
        """查看日志内容"""
        if not self.log_file or not os.path.exists(self.log_file):
            print("日志文件不存在")
            return
        with open(self.log_file, "r", encoding="utf-8") as f:
            print(f.read())

