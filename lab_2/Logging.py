import os
import datetime
import File
import WorkSpace

class Logger:
    """
    日志模块核心类 (Observer)
    负责监听命令执行并持久化到日志文件
    """
    def __init__(self):
        # 存储已启用日志的文件路径集合
        self._enabled_files = set()
        # 记录本次会话是否已经为某个文件写入过 Session Header，防止重复写入
        self._session_started = set()

    def enable_logging(self, filepath):
        """
        为指定文件启用日志
        """
        if filepath not in self._enabled_files:
            self._enabled_files.add(filepath)
            self._write_session_start(filepath)
            print(f"日志已启用: {self._get_log_filename(filepath)}")

    def disable_logging(self, filepath):
        """
        为指定文件关闭日志
        """
        if filepath in self._enabled_files:
            self._enabled_files.remove(filepath)
            print(f"日志已关闭: {filepath}")

    def is_logging_enabled(self, filepath):
        """检查文件是否开启了日志"""
        return filepath in self._enabled_files

    def log_command(self, filepath, command_str):
        """
        记录命令 (Observer 的 update 方法)
        :param filepath: 当前操作的文件路径
        :param command_str: 执行的命令字符串
        """
        if filepath not in self._enabled_files:
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
        log_entry = f"{timestamp} {command_str}\n"
        
        self._append_to_log_file(filepath, log_entry)

    def show_log(self, filepath):
        """
        读取并返回日志内容
        """
        log_file = self._get_log_filename(filepath)
        if not os.path.exists(log_file):
            return "暂无日志记录。"
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"读取日志失败: {str(e)}"

    def _get_log_filename(self, filepath):
        """
        获取日志文件名，格式为 .filename.log
        例如: lab.txt -> .lab.txt.log
        """
        dir_name, base_name = os.path.split(filepath)
        log_name = f".{base_name}.log"
        return os.path.join(dir_name, log_name)

    def _write_session_start(self, filepath):
        """
        写入会话开始标记
        """
        # 确保每次程序启动后，对每个文件只写入一次 session start
        if filepath in self._session_started:
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
        header = f"session start at {timestamp}\n"
        self._append_to_log_file(filepath, header)
        self._session_started.add(filepath)

    def _append_to_log_file(self, filepath, content):
        """
        写入文件系统的底层方法，包含错误处理
        """
        log_file = self._get_log_filename(filepath)
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            # 需求：若日志记录失败仅提示警告，不中断程序正常运行
            print(f"[Warning] 写入日志失败: {str(e)}")

class LogOnCommand:
    """
    命令: log-on [file]
    功能: 启用日志
    """
    def execute(self, command):
        parts = command.split(' ')
        if len(parts) < 2:
            # 默认对当前活动文件生效
            if not WorkSpace.WorkSpace.current_workFile_path:
                print("没有打开的文件")
            else:
                target_file = WorkSpace.WorkSpace.current_workFile_path
                if not target_file:
                    print("当前文件不存在")
                else:
                    WorkSpace.WorkSpace.logger.enable_logging(target_file)
        else:
            # 对指定文件生效
            target_file = parts[1]
            if(target_file not in File.FileList.all_files_path):
                print("当前文件不存在")
            else:
                WorkSpace.WorkSpace.logger.enable_logging(target_file)

class LogOffCommand:
    """
    命令: log-off [file]
    功能: 关闭日志
    """
    def execute(self, command):
        parts = command.split(' ')
        if len(parts) < 2:
            # 默认对当前活动文件生效
            if not WorkSpace.WorkSpace.current_workFile_path:
                print("没有打开的文件")
            else:
                # 获取当前文件路径
                target_path = WorkSpace.WorkSpace.current_workFile_path
                # 检查文件是否在当前工作区列表中
                if target_path not in WorkSpace.WorkSpace.current_workFile_list:
                    print("当前文件不存在")
                else:
                    WorkSpace.WorkSpace.logger.disable_logging(target_path)
        else:
            # 对指定文件生效
            target_file = parts[1]
            if(target_file not in File.FileList.all_files_path):
                print("当前文件不存在")
            else:
                WorkSpace.WorkSpace.logger.disable_logging(target_file)
            
class LogShowCommand:
    """
    命令: log-show [file]
    功能: 显示日志内容
    """
    def execute(self, command):
        parts = command.split(' ')
        if len(parts) < 2:
            # 默认对当前活动文件生效
            if not WorkSpace.WorkSpace.current_workFile_path:
                print("没有打开的文件")
            else:
                target_path = WorkSpace.WorkSpace.current_workFile_path
                if target_path not in WorkSpace.WorkSpace.current_workFile_list:
                    print("当前文件不存在")
                else:
                    content = WorkSpace.WorkSpace.logger.show_log(target_path)
                    print(f"--- Log for {target_path} ---")
                    print(content)
                    print("-----------------------------")
        else:
            # 对指定文件生效
            target_file = parts[1]
            if(target_file not in File.FileList.all_files_path):
                print("当前文件不存在")
            else:
                content = WorkSpace.WorkSpace.logger.show_log(target_file)
                print(f"--- Log for {target_file} ---")
                print(content)
                print("-----------------------------")