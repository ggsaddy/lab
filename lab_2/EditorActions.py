"""
编辑器操作命令模块
使用命令模式（Command Pattern）实现可撤销的编辑操作
"""
import WorkSpace
import Logging

class EditCommand:
    """编辑命令基类（抽象命令）"""
    
    def execute(self, command):
        """执行命令"""
        raise NotImplementedError
    
    def undo(self):
        """撤销命令"""
        raise NotImplementedError
    
    def can_undo(self):
        """判断是否可以撤销"""
        return True


class AppendCommand(EditCommand):
    """追加文本命令 - append "text" """
    
    def __init__(self):
        self.file = None
        self.text = ""
    
    def execute(self, command):
        # 解析命令：append "text"
        parts = command.split('"')
        if len(parts) < 2:
            print("参数错误，应为：append \"text\"")
            return False
        
        self.text = parts[1]
        
        # 获取当前活动文件
        if not WorkSpace.WorkSpace.current_workFile_path:
            print("没有打开的文件")
            return False
        
        self.file = WorkSpace.WorkSpace.current_workFile_list.get(
            WorkSpace.WorkSpace.current_workFile_path
        )
        
        if not self.file:
            print("当前文件不存在")
            return False
        
        # 执行追加操作
        self.file.content.append(self.text)
        self.file.state = "modified"
        print("追加成功")
        WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"append \"{self.text}\"")
        
        # 添加到命令历史（用于undo/redo）
        self.file.add_to_history(self)
        return True
    
    def undo(self):
        """撤销追加操作 - 删除最后一行"""
        if self.file and self.file.content:
            self.file.content.pop()
            print("撤销追加操作成功")
            WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"undo append \"{self.text}\"")
    
    def redo(self):
        """重做追加操作"""
        if self.file:
            self.file.content.append(self.text)
            print("重做追加操作成功")
            WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"redo append \"{self.text}\"")
        

class InsertCommand(EditCommand):
    """插入文本命令 - insert <line:col> "text" """
    
    def __init__(self):
        self.file = None
        self.line = 0
        self.col = 0
        self.text = ""
        self.original_line_content = ""
    
    def execute(self, command):
        # 解析命令：insert 1:3 "text"
        try:
            parts = command.split('"')
            if len(parts) < 2:
                print("参数错误，应为：insert <line:col> \"text\"")
                return False
            
            self.text = parts[1]
            position = parts[0].strip().split()[1]  # 获取line:col部分
            line_col = position.split(':')
            self.line = int(line_col[0])
            self.col = int(line_col[1])
            
        except (IndexError, ValueError):
            print("参数错误，应为：insert <line:col> \"text\"")
            return False
        
        # 获取当前活动文件
        if not WorkSpace.WorkSpace.current_workFile_path:
            print("没有打开的文件")
            return False
        
        self.file = WorkSpace.WorkSpace.current_workFile_list.get(
            WorkSpace.WorkSpace.current_workFile_path
        )
        
        if not self.file:
            print("当前文件不存在")
            return False
        
        # 行列号从1开始，转换为索引（从0开始）
        line_idx = self.line - 1
        col_idx = self.col - 1
        
        # 空文件只能在1:1插入
        if not self.file.content:
            if self.line != 1 or self.col != 1:
                print("空文件只能在1:1位置插入")
                return False
            self.file.content.append(self.text)
            self.file.state = "modified"
            print("插入成功")
            self.file.add_to_history(self)
            return True
        
        # 检查行号是否越界
        if line_idx < 0 or line_idx >= len(self.file.content):
            print("行号越界")
            return False
        
        # 检查列号是否越界
        current_line = self.file.content[line_idx]
        if col_idx < 0 or col_idx > len(current_line):
            print("列号越界")
            return False
        
        # 保存原始行内容（用于撤销）
        self.original_line_content = current_line
        
        # 处理包含换行符的文本
        if '\\n' in self.text:
            # 替换转义的换行符
            text_with_newlines = self.text.replace('\\n', '\n')
            lines = text_with_newlines.split('\n')
            
            # 拆分当前行
            before = current_line[:col_idx]
            after = current_line[col_idx:]
            
            # 第一行：before + lines[0]
            # 中间行：lines[1:-1]
            # 最后一行：lines[-1] + after
            new_lines = []
            new_lines.append(before + lines[0])
            for i in range(1, len(lines) - 1):
                new_lines.append(lines[i])
            new_lines.append(lines[-1] + after)
            
            # 替换原来的行并插入新行
            self.file.content[line_idx:line_idx+1] = new_lines
        else:
            # 简单插入
            new_line = current_line[:col_idx] + self.text + current_line[col_idx:]
            self.file.content[line_idx] = new_line
        
        self.file.state = "modified"
        print("插入成功")
        WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"insert {self.line}:{self.col} \"{self.text}\"")
        self.file.add_to_history(self)
        return True
    
    def undo(self):
        """撤销插入操作 - 恢复原始行内容"""
        if self.file:
            line_idx = self.line - 1
            
            # 如果原始行内容为空，说明是在空文件中插入的第一行
            if not self.original_line_content and len(self.file.content) == 1:
                self.file.content.pop()
            elif '\\n' in self.text:
                # 如果插入了多行，需要删除这些行并恢复原来的单行
                text_with_newlines = self.text.replace('\\n', '\n')
                lines_inserted = len(text_with_newlines.split('\n'))
                if self.original_line_content:
                    self.file.content[line_idx:line_idx+lines_inserted] = [self.original_line_content]
                else:
                    # 如果原始行内容为空，直接删除插入的行
                    del self.file.content[line_idx:line_idx+lines_inserted]
            else:
                # 恢复原始行内容
                if line_idx < len(self.file.content):
                    if self.original_line_content:
                        self.file.content[line_idx] = self.original_line_content
                    else:
                        # 如果原始行内容为空，删除该行
                        self.file.content.pop(line_idx)
            print("撤销插入操作成功")
            WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"undo insert {self.line}:{self.col} \"{self.text}\"")
    
    def redo(self):
        """重做插入操作"""
        if self.file:
            line_idx = self.line - 1
            col_idx = self.col - 1
            
            if '\\n' in self.text:
                # 处理多行插入
                text_with_newlines = self.text.replace('\\n', '\n')
                lines = text_with_newlines.split('\n')
                current_line = self.file.content[line_idx]
                before = current_line[:col_idx]
                after = current_line[col_idx:]
                
                new_lines = []
                new_lines.append(before + lines[0])
                for i in range(1, len(lines) - 1):
                    new_lines.append(lines[i])
                new_lines.append(lines[-1] + after)
                
                self.file.content[line_idx:line_idx+1] = new_lines
            else:
                # 简单插入
                current_line = self.file.content[line_idx]
                new_line = current_line[:col_idx] + self.text + current_line[col_idx:]
                self.file.content[line_idx] = new_line
            
            print("重做插入操作成功")
            WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"redo insert {self.line}:{self.col} \"{self.text}\"")


class DeleteCommand(EditCommand):
    """删除字符命令 - delete <line:col> <len> """
    
    def __init__(self):
        self.file = None
        self.line = 0
        self.col = 0
        self.length = 0
        self.deleted_text = ""
        self.original_line_content = ""
    
    def execute(self, command):
        # 解析命令：delete 1:3 5
        try:
            parts = command.split()
            if len(parts) != 3:
                print("参数错误，应为：delete <line:col> <len>")
                return False
            
            position = parts[1]
            line_col = position.split(':')
            self.line = int(line_col[0])
            self.col = int(line_col[1])
            self.length = int(parts[2])
            
        except (IndexError, ValueError):
            print("参数错误，应为：delete <line:col> <len>")
            return False
        
        # 获取当前活动文件
        if not WorkSpace.WorkSpace.current_workFile_path:
            print("没有打开的文件")
            return False
        
        self.file = WorkSpace.WorkSpace.current_workFile_list.get(
            WorkSpace.WorkSpace.current_workFile_path
        )
        
        if not self.file:
            print("当前文件不存在")
            return False
        
        # 行列号从1开始，转换为索引（从0开始）
        line_idx = self.line - 1
        col_idx = self.col - 1
        
        # 检查行号是否越界
        if line_idx < 0 or line_idx >= len(self.file.content):
            print("行号越界")
            return False
        
        # 检查列号是否越界
        current_line = self.file.content[line_idx]
        if col_idx < 0 or col_idx >= len(current_line):
            print("列号越界")
            return False
        
        # 检查删除长度是否超出行尾
        if col_idx + self.length > len(current_line):
            print("删除长度超出行尾")
            return False
        
        # 保存原始行内容和被删除的文本（用于撤销）
        self.original_line_content = current_line
        self.deleted_text = current_line[col_idx:col_idx + self.length]
        
        # 执行删除
        new_line = current_line[:col_idx] + current_line[col_idx + self.length:]
        self.file.content[line_idx] = new_line
        
        self.file.state = "modified"
        print("删除成功")
        WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"delete {self.line}:{self.col} {self.length}")
        self.file.add_to_history(self)
        return True
    
    def undo(self):
        """撤销删除操作 - 恢复原始行内容"""
        if self.file:
            line_idx = self.line - 1
            if line_idx < len(self.file.content):
                self.file.content[line_idx] = self.original_line_content
            print("撤销删除操作成功")
            WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"undo delete {self.line}:{self.col} {self.length}")
    
    def redo(self):
        """重做删除操作"""
        if self.file:
            line_idx = self.line - 1
            col_idx = self.col - 1
            current_line = self.file.content[line_idx]
            new_line = current_line[:col_idx] + current_line[col_idx + self.length:]
            self.file.content[line_idx] = new_line
            print("重做删除操作成功")
            WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"redo delete {self.line}:{self.col} {self.length}")


class ReplaceCommand(EditCommand):
    """替换字符命令 - replace <line:col> <len> "text" """
    
    def __init__(self):
        self.file = None
        self.line = 0
        self.col = 0
        self.length = 0
        self.text = ""
        self.original_line_content = ""
    
    def execute(self, command):
        # 解析命令：replace 1:3 5 "text"
        try:
            parts = command.split('"')
            if len(parts) < 2:
                print("参数错误，应为：replace <line:col> <len> \"text\"")
                return False
            
            self.text = parts[1]
            cmd_parts = parts[0].strip().split()
            if len(cmd_parts) != 3:
                print("参数错误，应为：replace <line:col> <len> \"text\"")
                return False
            
            position = cmd_parts[1]
            line_col = position.split(':')
            self.line = int(line_col[0])
            self.col = int(line_col[1])
            self.length = int(cmd_parts[2])
            
        except (IndexError, ValueError):
            print("参数错误，应为：replace <line:col> <len> \"text\"")
            return False
        
        # 获取当前活动文件
        if not WorkSpace.WorkSpace.current_workFile_path:
            print("没有打开的文件")
            return False
        
        self.file = WorkSpace.WorkSpace.current_workFile_list.get(
            WorkSpace.WorkSpace.current_workFile_path
        )
        
        if not self.file:
            print("当前文件不存在")
            return False
        
        # 行列号从1开始，转换为索引（从0开始）
        line_idx = self.line - 1
        col_idx = self.col - 1
        
        # 检查行号是否越界
        if line_idx < 0 or line_idx >= len(self.file.content):
            print("行号越界")
            return False
        
        # 检查列号是否越界
        current_line = self.file.content[line_idx]
        if col_idx < 0 or col_idx >= len(current_line):
            print("列号越界")
            return False
        
        # 检查替换长度是否超出行尾
        if col_idx + self.length > len(current_line):
            print("替换长度超出行尾")
            return False
        
        # 保存原始行内容（用于撤销）
        self.original_line_content = current_line
        
        # 执行替换：删除指定长度，然后插入新文本
        new_line = current_line[:col_idx] + self.text + current_line[col_idx + self.length:]
        self.file.content[line_idx] = new_line
        
        self.file.state = "modified"
        print("替换成功")
        self.file.add_to_history(self)
        WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"replace {self.line}:{self.col} {self.length} \"{self.text}\"")
        return True
    
    def undo(self):
        """撤销替换操作 - 恢复原始行内容"""
        if self.file:
            line_idx = self.line - 1
            if line_idx < len(self.file.content):
                self.file.content[line_idx] = self.original_line_content
            print("撤销替换操作成功")
            WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"undo replace {self.line}:{self.col} {self.length} \"{self.text}\"")
    
    def redo(self):
        """重做替换操作"""
        if self.file:
            line_idx = self.line - 1
            col_idx = self.col - 1
            current_line = self.file.content[line_idx]
            new_line = current_line[:col_idx] + self.text + current_line[col_idx + self.length:]
            self.file.content[line_idx] = new_line
            print("重做替换操作成功")
            WorkSpace.WorkSpace.logger.log_command(self.file.filePath, f"redo replace {self.line}:{self.col} {self.length} \"{self.text}\"")


class ShowCommand(EditCommand):
    """显示文本内容命令 - show [startLine:endLine] """
    
    def execute(self, command):
        # 获取当前活动文件
        if not WorkSpace.WorkSpace.current_workFile_path:
            print("没有打开的文件")
            return False
        
        file = WorkSpace.WorkSpace.current_workFile_list.get(
            WorkSpace.WorkSpace.current_workFile_path
        )
        
        if not file:
            print("当前文件不存在")
            return False
        
        # 解析命令：show 或 show 1:5
        parts = command.split()
        
        if len(parts) == 1:
            # 显示全文
            start_line = 1
            end_line = len(file.content)
        elif len(parts) == 2:
            # 显示指定范围
            try:
                range_parts = parts[1].split(':')
                start_line = int(range_parts[0])
                end_line = int(range_parts[1])
            except (IndexError, ValueError):
                print("参数错误，应为：show [startLine:endLine]")
                return False
        else:
            print("参数错误，应为：show [startLine:endLine]")
            return False
        
        # 处理空文件
        if not file.content:
            print("(空文件)")
            return False
        
        # 检查范围
        if start_line < 1 or end_line < start_line:
            print("行号范围错误")
            return False
        
        if start_line > len(file.content):
            print("起始行号超出文件范围")
            return False
        
        # 显示内容
        actual_end = min(end_line, len(file.content))
        for i in range(start_line - 1, actual_end):
            print(f"{i + 1}: {file.content[i]}")
        
        WorkSpace.WorkSpace.logger.log_command(file, f"show {start_line}:{end_line}")
        return False  # show命令不进入历史栈
    
    def can_undo(self):
        """show命令不能撤销"""
        return False
