import json
from datetime import datetime
from File import FileList

def update(current_workFile_path, current_workFile_list):
    new_state = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_workFile_path": current_workFile_path,

        "current_workFile_list": {
            filePath: fileObj.state
            for filePath, fileObj in current_workFile_list.items()
        },

        # 保存所有文件
        "all_files": [
            {
                "fileName": f.fileName,
                "filePath": f.filePath,
                "content": f.content,
                "state": f.state
            }
            for f in FileList.all_files.values()
        ]
    }

    # 读取原来的状态历史（list）
    try:
        with open("memento.txt", "r", encoding="utf-8") as f:
            all_states = json.load(f)
    except FileNotFoundError:
        all_states = []

    # 添加新的快照
    all_states.append(new_state)

    # 写回文件
    with open("memento.txt", "w", encoding="utf-8") as f:
        json.dump(all_states, f, ensure_ascii=False, indent=2)

    print("工作区状态已保存")


def recover():
    try:
        with open("memento.txt", "r", encoding="utf-8") as f:
            all_states = json.load(f)
    except FileNotFoundError:
        print("没有可恢复的工作区状态")
        return

    if not all_states:
        print("没有可恢复的工作区状态")
        return

    last_state = all_states[-1]

    return last_state