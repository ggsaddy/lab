import WorkSpace
import Memento
import EditorActions
import Logging

class CommandFactory:
    def __init__(self):
        self.commands = {
            # 工作区命令
            "load": WorkSpace.LoadCommand(),
            "save": WorkSpace.SaveCommand(),
            "init": WorkSpace.InitCommand(),
            "close": WorkSpace.CloseCommand(),
            "edit": WorkSpace.EditCommand(),
            "editor-list": WorkSpace.EditorListCommand(),
            "dir-tree": WorkSpace.DirTreeCommand(),
            "undo": WorkSpace.UndoCommand(),
            "redo": WorkSpace.RedoCommand(),

            # 文本编辑命令
            "append": EditorActions.AppendCommand(),
            "insert": EditorActions.InsertCommand(),
            "delete": EditorActions.DeleteCommand(),
            "replace": EditorActions.ReplaceCommand(),
            "show": EditorActions.ShowCommand(),

            # # 日志命令
            "log-on": Logging.LogOnCommand(),
            "log-off": Logging.LogOffCommand(),
            "log-show": Logging.LogShowCommand(),
        }

    def isValid(self, operator):
        return operator in self.commands

    def getCommand(self, operator):
        return self.commands.get(operator)
    
if __name__ == "__main__":
    cf=CommandFactory()
    last_state = Memento.recover()
    WorkSpace.WorkSpace.recover()
    while True:
        command = input("> ")
        if(command == "exit"):
            #退出的时候记录一下当前状态
            Memento.update(WorkSpace.WorkSpace.current_workFile_path,WorkSpace.WorkSpace.current_workFile_list)
            break
        #调试用
        if(command == "curpath"):
            print(WorkSpace.WorkSpace.current_workFile_path)
            continue
        if(command == "curlist"):
            print(WorkSpace.WorkSpace.current_workFile_list)
            continue
        operator = command.split(" ")[0]
        if(not cf.isValid(operator)):
            print("不支持的操作")
            continue
        cf.getCommand(operator).execute(command)
        
