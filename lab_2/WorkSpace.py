import File
import CommonUtils
from datetime import datetime
import Memento
import Logging

class WorkSpace():
    current_workFile_path = ""
    current_workFile_list = {}
    logOpen = False
    #这个用于lru
    recent_files = []
    
    # 集成 Logger 日志记录实例
    logger = Logging.Logger() 
    
    @classmethod
    #只有在 load close 时才会更新
    def update_current_workFile_list(self):
        Memento.update(self.current_workFile_path,self.current_workFile_list)
    
    @classmethod
    def update_current_workFile_path(self,filePath):
        WorkSpace.current_workFile_path = filePath
        Memento.update(self.current_workFile_path,self.current_workFile_list)

    @classmethod
    def recover(self):
        last_state = Memento.recover()
        if not last_state:
            return
        WorkSpace.current_workFile_path = last_state.get("current_workFile_path", "")

        WorkSpace.current_workFile_list.clear()
        File.FileList.all_files.clear()
        File.FileList.all_files_path.clear()
        WorkSpace.recent_files.clear()

        temp_files = {}

        for f in last_state.get("all_files", []):
            tf = File.TextFile(f["filePath"], content=f["content"])
            tf.state = f["state"]

            temp_files[f["filePath"]] = tf
            File.FileList.all_files[f["filePath"]] = tf
            File.FileList.all_files_path.add(f["filePath"])

        saved_list = last_state.get("current_workFile_list", {})
        current_file = None

        for filePath in saved_list.keys():
            if filePath in temp_files:
                WorkSpace.current_workFile_list[filePath] = temp_files[filePath]
                if filePath != WorkSpace.current_workFile_path:
                    WorkSpace.recent_files.append(filePath)
                else:
                    current_file = filePath

        #当前工作文件需要在最近列表最后
        if current_file:
            WorkSpace.recent_files.append(current_file)

class LoadCommand():
    def execute(self, command):
        if(len(command.split(" "))) != 2 :
            print("参数错误，应为：load <file>")
            return 
        filePath = command.split(" ")[1]
        if not CommonUtils.pathCheck(filePath):
            return 
        if filePath in WorkSpace.recent_files:
            print("当前文件已打开，请使用edit命令切换")
            return 
        curFile = None
        if(filePath not in File.FileList.all_files_path):
            curFile = CommonUtils.create_newFile(filePath)
        else:
            curFile = File.FileList.all_files[filePath]
            print(f"加载文件成功")
        WorkSpace.current_workFile_list[filePath]=curFile    
        WorkSpace.update_current_workFile_path(filePath)
        # 更新recent_files列表
        if filePath in WorkSpace.recent_files:
            WorkSpace.recent_files.remove(filePath)
        WorkSpace.recent_files.append(filePath)
        WorkSpace.logger.log_command(filePath, f"load {filePath}")

     
class SaveCommand():
    def execute(self, command):
        args = command.split(" ")
        if len(args) == 1:
            # save 当前文件
            filePath = WorkSpace.current_workFile_path
            self.save_single_file(filePath)
        elif len(args) == 2:
            param = args[1]
            if param == "all":
                # save 所有文件
                self.save_all_files()
            else:
                # save 指定文件
                filePath = param
                if not CommonUtils.pathCheck(filePath):
                    print("参数错误")
                    return
                if filePath not in [f.filePath for f in WorkSpace.current_workFile_list.values()]:
                    print("该文件不在当前工作区中")
                    return
                self.save_single_file(filePath)
                WorkSpace.logger.log_command(filePath, f"save {filePath}")
        else:
            print("参数错误，应为：save [file|all]")
            return

    def save_single_file(self, file_path):
        """保存单个文件"""
        # 检查是否有活动文件
        if not WorkSpace.current_workFile_path:
            print("没有打开的文件")
            return

        # 获取要保存的文件
        file_to_save = WorkSpace.current_workFile_list.get(file_path)
        if not file_to_save:
            print("文件不存在")
            return

        # 写入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for line in file_to_save.content:
                    f.write(line + '\n')
            # 更新文件状态
            file_to_save.state = "normal"
            print(f"保存文件 {file_path} 成功")
        except Exception as e:
            print(f"保存文件失败: {e}")

    def save_all_files(self):
        """保存所有已打开的文件"""
        if not WorkSpace.current_workFile_list:
            print("没有打开的文件")
            return
            
        for file_path, file_obj in WorkSpace.current_workFile_list.items():
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for line in file_obj.content:
                        f.write(line + '\n')
                # 更新文件状态
                file_obj.state = "normal"
                print(f"保存文件 {file_path} 成功")
            except Exception as e:
                print(f"保存文件 {file_path} 失败: {e}")
        
        print("所有文件保存完成")
        
               

class InitCommand():
    def execute(self, command):
        args = command.split(" ")
        filePath =""
        withLog = False
        if len(args)==3:
            if(not CommonUtils.pathCheck(args[1]) or args[2]!="with-log"):
                print("参数错误")
                return 
            filePath = args[1]
            withLog = True
        elif len(args)==2:
            if(not CommonUtils.pathCheck(args[1])):
                print("参数错误")
                return 
            filePath = args[1]
        else:
            print("参数错误")
            return
        if(filePath in File.FileList.all_files_path):
            print("文件已存在")
            return
        curFile = CommonUtils.create_newFile(filePath,withLog)
        WorkSpace.current_workFile_list[filePath]=curFile
        WorkSpace.update_current_workFile_path(filePath)
        if filePath in WorkSpace.recent_files:
            WorkSpace.recent_files.remove(filePath)
        WorkSpace.recent_files.append(filePath)
        print("初始化文件成功")
        if withLog:
            WorkSpace.logger.enable_logging(filePath)
            WorkSpace.logger.log_command(filePath, f"init {filePath} with-log")
        else:
            WorkSpace.logger.log_command(filePath, f"init {filePath}")

class CloseCommand():
    def execute(self, command):
        args = command.split(" ")
        if len(args) == 1:
            filePath = WorkSpace.current_workFile_path
        elif len(args) == 2:
            filePath = args[1]
            if not CommonUtils.pathCheck(filePath):
                print("参数错误")
                return
            if filePath not in [f.filePath for f in WorkSpace.current_workFile_list.values()]:
                print("该文件不在当前工作区中")
                return
        else:
            print("参数错误")
            return
        curFile = WorkSpace.current_workFile_list[filePath]
        if(curFile.state=="modified"):
            op=input("文件已修改，是否保存文件？(y/n)")
            if(op == "y"):
                #这里调save 的操作
                SaveCommand().execute(f"save {filePath}")
            elif(op == "n"):
                #n 就直接关闭
                del WorkSpace.current_workFile_list[filePath]
                WorkSpace.recent_files.remove(filePath)
                if(filePath == WorkSpace.current_workFile_path and WorkSpace.recent_files):
                    WorkSpace.update_current_workFile_path(WorkSpace.recent_files[-1])
                else:
                    WorkSpace.update_current_workFile_path("")
            else:
                print("参数错误")
        else:
            del WorkSpace.current_workFile_list[filePath]
            WorkSpace.recent_files.remove(filePath)
            if(filePath == WorkSpace.current_workFile_path and WorkSpace.recent_files):
                WorkSpace.update_current_workFile_path(WorkSpace.recent_files[-1])
            else:
                WorkSpace.update_current_workFile_path("")
        WorkSpace.update_current_workFile_list()
        print("关闭文件成功")
        WorkSpace.logger.log_command(filePath, f"close {filePath}")


class EditCommand():
    def execute(self, command):
        if(len(command.split(" "))) != 2 :
            print("参数错误，应为：edit <file>")
            return
        filePath = command.split(" ")[1]
        if not CommonUtils.pathCheck(filePath):
                print("参数错误")
                return
        if filePath not in [f.filePath for f in WorkSpace.current_workFile_list.values()]:
            print("该文件不在当前工作区中")
            return
        
        WorkSpace.update_current_workFile_path(filePath)
        #把当前文件放到recent的最后
        if filePath in WorkSpace.recent_files:
            WorkSpace.recent_files.remove(filePath)
        WorkSpace.recent_files.append(filePath)
        print(f"切换到文件{filePath}成功")
        WorkSpace.logger.log_command(filePath, f"edit {filePath}")

class EditorListCommand():
    def execute(self, command):
        if(len(command.split(" "))) != 1 :
            print("参数错误，应为：editor-list")
        for f in WorkSpace.current_workFile_list.values():
            print(f.filePath)

class DirTreeCommand():
    def execute(self, command):
        if len(command.split(" ")) != 1:
            print("参数错误，应为：dir-tree")
            return

        paths = list(File.FileList.all_files_path)
        if not paths:
            print("(空)")
            return
        tree = {}

        for filePath in paths:
            parts = filePath.split("/")
            cur = tree
            for p in parts:
                if p not in cur:
                    cur[p] = {}
                cur = cur[p]

        def print_tree(node, indent=""):
            keys = list(node.keys())
            total = len(keys)
            for i, key in enumerate(keys):
                is_last = (i == total - 1)
                prefix = "└── " if is_last else "├── "
                print(indent + prefix + key)

                # 如果还有下级目录，继续打印
                next_indent = indent + ("    " if is_last else "│   ")
                print_tree(node[key], next_indent)

        print_tree(tree)

class UndoCommand():
    def execute(self, command):
        if len(command.split()) != 1:
            print("参数错误，应为：undo")
            return
        
        # 检查是否有活动文件
        if not WorkSpace.current_workFile_path:
            print("没有打开的文件")
            return
        
        # 获取当前文件
        current_file = WorkSpace.current_workFile_list.get(WorkSpace.current_workFile_path)
        if not current_file:
            print("当前文件不存在")
            return
        
        # 执行撤销
        current_file.undo()
        WorkSpace.logger.log_command(current_file, f"undo {current_file}")

class RedoCommand():
    def execute(self, command):
        if len(command.split()) != 1:
            print("参数错误，应为：redo")
            return
        
        # 检查是否有活动文件
        if not WorkSpace.current_workFile_path:
            print("没有打开的文件")
            return
        
        # 获取当前文件
        current_file = WorkSpace.current_workFile_list.get(WorkSpace.current_workFile_path)
        if not current_file:
            print("当前文件不存在")
            return
        
        # 执行重做
        current_file.redo()
        WorkSpace.logger.log_command(current_file, f"redo {current_file}")