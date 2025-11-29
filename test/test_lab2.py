import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.workspace import Workspace
from core.logger import Logger
from core.statistics import Statistics
from core.commands import AppendCommand, InsertCommand, DeleteCommand, ReplaceCommand
from core.xml_commands import (
    InsertBeforeCommand,
    AppendChildCommand,
    EditIdCommand,
    EditTextCommand,
    DeleteElementCommand,
)
from core.spellcheck import SimpleSpellChecker, LanguageToolHTTPSpellChecker


def assert_eq(desc, a, b):
    ok = (a == b)
    print(f"[{'PASS' if ok else 'FAIL'}] {desc}: {a} == {b}")
    return ok


def run_lab1_tests():
    print("=== Lab1: Text Editor & Workspace & Logger ===")
    w = Workspace(); log = Logger(); stat = Statistics(); w.attach(log); w.attach(stat)

    # init text with log
    w.init_file("lab1_demo.txt", with_log=True)
    ed = w.active_editor
    # append
    # 注意：初始化时可能包含首行 '# log'，我们在后续断言时做对应调整
    ed.execute_command(AppendCommand(ed, "Hello World"))
    ed.execute_command(AppendCommand(ed, "This is line 2"))
    # insert 到第一行有效文本（如果首行是 '# log'，则目标行+1）
    target_line = 1
    if ed.lines and ed.lines[0].strip().startswith('# log'):
        target_line = 2
    ed.execute_command(InsertCommand(ed, target_line, 6, " Python"))
    # undo/redo
    ed.undo(); ed.redo()
    # delete 对应行的 ' Python'
    ed.execute_command(DeleteCommand(ed, target_line, 6, 7))
    # replace
    # replace 第二行 'line' 为 'Code'（若有 '# log'，第二行是 Hello World，则第三行是 This is line 2）
    replace_line = 2 if target_line == 1 else 3
    ed.execute_command(ReplaceCommand(ed, replace_line, 9, 4, "Code"))
    w.save_file()

    # show-like check
    print("-- Content after operations --")
    for i, line in enumerate(ed.lines, start=1):
        print(f"{i}: {line}")
    # 根据是否存在 '# log' 行断言内容
    if ed.lines and ed.lines[0].strip().startswith('# log'):
        assert_eq("Line2", ed.lines[1], "Hello World")
        assert_eq("Line3", ed.lines[2], "This is Code 2")
    else:
        assert_eq("Line1", ed.lines[0], "Hello World")
        assert_eq("Line2", ed.lines[1], "This is Code 2")

    # editor-list with duration
    print("-- editor-list with duration --")
    w.list_editors()

    # log-on/off/show
    w.notify("log_on", {"filename": ed.filename})
    w.notify("command", {"filename": ed.filename, "command_str": "append \"Test\""})
    w.notify("log_off", {"filename": ed.filename})

    # close file (should prompt save; we simulate already saved)
    w.close_file(ed.filename)


def run_lab2_text_spellcheck():
    print("=== Lab2: Spell Check for Text ===")
    w = Workspace(); log = Logger(); stat = Statistics(); w.attach(log); w.attach(stat)
    w.init_file("lab2_text.txt", with_log=False)
    ed = w.active_editor
    ed.execute_command(AppendCommand(ed, "This line has recieve and occured."))
    sp = LanguageToolHTTPSpellChecker(force_offline=True)
    findings = sp.check_text(ed.lines)
    print("-- spell-check findings (text) --")
    for f in findings:
        print(f)
    # expect at least two findings
    assert_eq("findings>=2", len(findings) >= 2, True)


def run_lab2_xml_editor():
    print("=== Lab2: XML Editor & Commands ===")
    w = Workspace(); log = Logger(); stat = Statistics(); w.attach(log); w.attach(stat)
    w.init_file("lab2_xml.xml", with_log=True)
    xe = w.active_editor
    # append-child
    xe.execute_command(AppendChildCommand(xe, "book", "book1", "root", None))
    xe.execute_command(AppendChildCommand(xe, "title", "title1", "book1", "Itallian"))
    # insert-before
    xe.execute_command(InsertBeforeCommand(xe, "book", "book0", "book1", None))
    # edit-id
    xe.execute_command(EditIdCommand(xe, "book1", "book001"))
    # edit-text
    xe.execute_command(EditTextCommand(xe, "title1", "Itallian by Rowlling"))
    # xml-tree
    print("-- xml-tree --")
    for line in xe.xml_tree_lines():
        print(line)
    # basic structure check
    assert_eq("has root", xe.root.tag, "root")
    assert_eq("has title1 text", xe.id_index["title1"].text, "Itallian by Rowlling")
    # delete element
    xe.execute_command(DeleteElementCommand(xe, "book0"))
    assert_eq("book0 deleted", "book0" in xe.id_index, False)
    w.save_file("lab2_xml.xml")
    # attempt invalid operations
    print("-- invalid xml operations --")
    xe.execute_command(EditIdCommand(xe, "root", "newroot"))  # should print warning
    xe.execute_command(InsertBeforeCommand(xe, "x", "x1", "root", None))  # cannot insert before root
    xe.execute_command(DeleteElementCommand(xe, "root"))  # cannot delete root


def run_lab2_xml_spellcheck():
    print("=== Lab2: Spell Check for XML ===")
    w = Workspace(); log = Logger(); stat = Statistics(); w.attach(log); w.attach(stat)
    w.init_file("lab2_xml2.xml", with_log=False)
    xe = w.active_editor
    xe.execute_command(AppendChildCommand(xe, "title", "titleA", "root", "Itallian by Rowlling"))
    sp = LanguageToolHTTPSpellChecker(force_offline=True)
    elements = [(eid, e.text) for eid, e in xe.id_index.items() if e.text]
    findings = sp.check_xml_texts(elements)
    print("-- spell-check findings (xml) --")
    for f in findings:
        print(f)
    assert_eq("xml findings>=1", len(findings) >= 1, True)


def run_editor_list_duration():
    print("=== Lab2: Statistics editor-list ===")
    w = Workspace(); log = Logger(); stat = Statistics(); w.attach(log); w.attach(stat)
    w.init_file("a.txt", with_log=False)
    w.init_file("b.xml", with_log=False)
    # switch to accumulate some time
    import time
    time.sleep(1.2)
    w.switch_editor("a.txt")
    time.sleep(1.2)
    w.switch_editor("b.xml")
    time.sleep(1.2)
    print("-- editor-list with durations --")
    w.list_editors()


def run_log_filter_test():
    print("=== Lab2: Logger filter assertions ===")
    fname = "log_filter.xml"
    try:
        if os.path.exists(f".{fname}.log"):
            os.remove(f".{fname}.log")
    except OSError:
        pass
    with open(fname, "w", encoding="utf-8") as f:
        f.write("# log -e insert-before -e append-child -e append\n")
        f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<root id=\"root\"></root>\n")

    w = Workspace(); log = Logger(); stat = Statistics(); w.attach(log); w.attach(stat)
    w.load_file(fname)
    xe = w.active_editor
    xe.execute_command(AppendChildCommand(xe, "title", "title1", "root", "foo"))
    w.notify("command", {"filename": fname, "command_str": "append-child title title1 root \"foo\""})
    xe.execute_command(InsertBeforeCommand(xe, "title", "title0", "title1", ""))
    w.notify("command", {"filename": fname, "command_str": "insert-before title title0 title1 \"\""})
    xe.execute_command(EditTextCommand(xe, "title1", "bar"))
    w.notify("command", {"filename": fname, "command_str": "edit-text title1 \"bar\""})

    try:
        with open(f".{fname}.log", "r", encoding="utf-8") as lf:
            content = lf.read()
    except FileNotFoundError:
        content = ""
    print("-- log content --\n" + content)
    assert_eq("contains edit-text", "edit-text" in content, True)
    assert_eq("no append-child logged", "append-child" in content, False)
    assert_eq("no insert-before logged", "insert-before" in content, False)
    # 文本命令过滤验证：在该文件上执行 append 的通知也应被过滤
    w.notify("command", {"filename": fname, "command_str": "append \"TEST\""})
    try:
        with open(f".{fname}.log", "r", encoding="utf-8") as lf:
            content2 = lf.read()
    except FileNotFoundError:
        content2 = ""
    assert_eq("no append logged (text cmd)", "append \"TEST\"" in content2, False)


def main():
    run_lab1_tests()
    run_lab2_text_spellcheck()
    run_lab2_xml_editor()
    run_lab2_xml_spellcheck()
    run_editor_list_duration()
    run_log_filter_test()
    run_text_out_of_bounds_tests()
    run_dir_tree_test()
    run_statistics_boundary_tests()
    run_spell_http_tests()
    run_workspace_memento_tests()
    print("=== All tests executed ===")

def run_text_out_of_bounds_tests():
    print("=== Lab1: Text Editor OOB assertions ===")
    w = Workspace(); log = Logger(); stat = Statistics(); w.attach(log); w.attach(stat)
    w.init_file("oob.txt", with_log=False)
    ed = w.active_editor
    ed.execute_command(AppendCommand(ed, "abcdef"))
    # insert col out of range
    ok = ed.execute_command(InsertCommand(ed, 1, 999, "x"))
    print("insert OOB executed:", ok)
    # delete length exceeds
    ok2 = ed.execute_command(DeleteCommand(ed, 1, 4, 99))
    print("delete OOB executed:", ok2)
    # replace range out of bounds
    ok3 = ed.execute_command(ReplaceCommand(ed, 1, 4, 99, "X"))
    print("replace OOB executed:", ok3)
    assert_eq("insert OOB == False", ok, False)
    assert_eq("delete OOB == False", ok2, False)
    assert_eq("replace OOB == False", ok3, False)

def run_dir_tree_test():
    print("=== Dir-tree output assertions ===")
    # create small structure
    os.makedirs("tmp_dir/sub", exist_ok=True)
    with open("tmp_dir/a.txt", "w") as f: f.write("hello\n")
    with open("tmp_dir/sub/b.txt", "w") as f: f.write("world\n")
    from utils.file_helper import print_dir_tree
    print_dir_tree("tmp_dir")
    # basic assertion: visually verify the printed tree includes branch characters
    print("(manual check) dir-tree printed with branching characters")

def run_statistics_boundary_tests():
    print("=== Statistics boundary format assertions ===")
    st = Statistics()
    # simulate durations using private fields (simple, since there is no injection of time source)
    st._durations["sec.txt"] = 45
    st._durations["min.txt"] = 75
    st._durations["hour.txt"] = 2 * 3600 + 15 * 60
    st._durations["day.txt"] = 1 * 24 * 3600 + 3 * 3600
    print("sec:", st.get_duration_str("sec.txt"))
    print("min:", st.get_duration_str("min.txt"))
    print("hour:", st.get_duration_str("hour.txt"))
    print("day:", st.get_duration_str("day.txt"))
    assert_eq("sec format", st.get_duration_str("sec.txt"), "45秒")
    assert_eq("min format", st.get_duration_str("min.txt"), "1分钟")
    assert_eq("hour format", st.get_duration_str("hour.txt"), "2小时15分钟")
    assert_eq("day format", st.get_duration_str("day.txt"), "1天3小时")
    # in-session accumulation: active_start increases display
    st._start_at["sec.txt"] = st._durations["sec.txt"] - 5 + 1  # fake start time using offset of time.time()
    # We cannot rewire time.time() easily; here we just ensure call path is exercised
    print("accumulated (session ongoing):", st.get_duration_str("sec.txt"))

def run_spell_http_tests():
    print("=== Spell HTTP adapter assertions ===")
    # mock request_fn that returns one match for 'recieve' -> 'receive'
    def mock_request(text: str, lang: str):
        # find first occurrence of 'recieve'
        idx = text.find('recieve')
        if idx == -1:
            return {"matches": []}
        return {"matches": [{"offset": idx, "length": len('recieve'), "replacements": [{"value": "receive"}]}]}

    from core.spellcheck import LanguageToolHTTPSpellChecker
    lines = ["This line has recieve."]
    sp = LanguageToolHTTPSpellChecker(force_offline=False, request_fn=mock_request)
    res = sp.check_text(lines)
    print("http text results:", res)
    assert_eq("http returns suggestion", len(res) >= 1, True)
    # xml variant
    elems = [("x1", "recieve here")]
    res2 = sp.check_xml_texts(elems)
    print("http xml results:", res2)
    assert_eq("http xml returns", len(res2) >= 1, True)

def run_workspace_memento_tests():
    print("=== Workspace memento save/restore assertions ===")
    from core.workspace import Workspace
    from core.logger import Logger
    from core.statistics import Statistics
    w = Workspace(); log = Logger(); stat = Statistics(); w.attach(log); w.attach(stat)
    # open two files and modify one
    w.init_file("memo1.txt", with_log=True)
    ed1 = w.active_editor
    ed1.execute_command(AppendCommand(ed1, "A"))
    w.init_file("memo2.xml", with_log=False)
    ed2 = w.active_editor
    ed2.execute_command(AppendChildCommand(ed2, "title", "t1", "root", "B"))
    # enable logging manually for xml
    w.notify("log_on", {"filename": "memo2.xml"})
    # save state
    w.save_state()
    print("saved memento")
    # construct new workspace and restore
    w2 = Workspace(); log2 = Logger(); stat2 = Statistics(); w2.attach(log2); w2.attach(stat2)
    w2.load_workspace_state()
    # assertions
    print("restored active:", w2.active_editor_name)
    assert_eq("restored active == memo2.xml", w2.active_editor_name, "memo2.xml")
    # modified flags restored
    assert_eq("memo1 modified", w2.editors["memo1.txt"].is_modified, True)
    assert_eq("memo2 modified", w2.editors["memo2.xml"].is_modified, True)
    # logging restored (via notify in restore)
    enabled = log2.get_enabled_files()
    print("logging enabled after restore:", enabled)
    assert_eq("log restored contains memo2.xml", "memo2.xml" in enabled, True)


if __name__ == "__main__":
    main()
