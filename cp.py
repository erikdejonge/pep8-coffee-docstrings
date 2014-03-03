#!/usr/bin/python
# coding=utf-8
"""
cp.py
"""
import os
import time
from argparse import ArgumentParser
import sys
reload(sys)
#noinspection PyUnresolvedReferences
sys.setdefaultencoding("utf-8")

ADDCOMMENT_WITH_FOUND_TYPE = False

datastructure_define = False


def replace_variables():
    """
    @return: @rtype:
    """
    variables = ["utils.print_once", "print", "warning", "emit_event", "urls.command", "urls.postcommand", "async_call_retries", "utils.set_time_out", "utils.set_interval"]
    undo_variables = []
    watch_variables = []
    color_vals_to_keep = ['91m', '92m', '94m', '95m', '41m', '97m']
    return color_vals_to_keep, undo_variables, variables, watch_variables


def func_test(funcs, line):
    """

    @param funcs:
    @param line:
    @return: @rtype:
    """
    for func in funcs:
        res = func(line)
        if res:
            return True
    return False


def global_class_declare(line):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip().find("=") == len(line.strip()) - 1:
        if line.find(" ") != 0:
            return True
    return False


def on_scope(line):
    """

    @param line:
    @return: @rtype:
    """
    return line.strip().find("$scope.") == 0


def anon_func(line):
    """

    @param line:
    @return: @rtype:
    """
    line = str(line)
    if in_test(["warning", "print"], line):
        return False
    if "->" in line:
        return True
    if "=>" in line:
        return True
    return False


def parenthesis(line):
    """

    @param line:
    @return: @rtype:
    """
    return ("(" in line) and (")" in line)


def anon_func_param(line):
    """

    @param line:
    @return: @rtype:
    """
    if functional(line):
        return False

    line = str(line)
    return parenthesis(line) and anon_func(line)


def functional(line):
    """

    @param line:
    @return: @rtype:
    """
    if "_." in line:
        return True
    return False


def func_def(line):
    """

    @param line:
    @return: @rtype:
    """

    if in_test(["+=", "-=", "++", "--", "*="], line):
        return False


    if ", ->" in line.strip():
        return True
    if ", ->" in line.strip():
        return True

    elif line.strip().startswith("def "):
        return True
    elif functional(line):
        return False
    line = str(line)

    if in_test(["warning", "print "], line):
        return False

    is_func = ("->" in line or "=>" in line) and "= " in line

    if not is_func:
        if "def " in line and ":" in line:
            is_func = True

    return is_func


def method_call(line):
    """

    @param line:
    @return: @rtype:
    """

    if in_test(["+=", "-=", "++", "--", "*="], line):
        return False

    if line.strip().endswith(","):
        return False
    if line.count("(") == 1:
        if line.count("str(") == 1:
            return False
    line = str(line)
    if line.strip().find(":") > 0:
        return False
    #return (line.count("(") is 1 and line.count(")") is 1) or ("$(this)." in line and line.count("(") is 1 and line.count(")") is 1)
    return (line.count("(") > 0 and line.count(")") > 0) or ("$(this)." in line and line.count("(") > 0 and line.count(")") > 0)


def class_method(line):
    """

    @param line:
    @return: @rtype:
    """
    if "raise" in line:
        return False
    line = str(line)
    if in_test(["+=", "-=", "++", "--", "*="], line):
        return False
    if in_test(["print"], line):
        if not in_test([":", "->", "=>"], line):
            return False

    return ("->" in line or "=>" in line) and ":" in line


def scope_declaration(line):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip().find("$scope") == 0:
        return True
    return False


def scoped_method_call(line):
    """

    @param line:
    @return: @rtype:
    """
    if functional(line):
        return False

    if in_test(["warning", "print"], line):
        return False

    line = str(line)
    return ("= " in line and ("->" in line or "=>" in line)) or (scope_declaration(line) and "()" in line and line.find("     ") is not 0)


def some_func(line):
    """

    @param line:
    @return: @rtype:
    """
    return func_test([func_def, class_method, scoped_method_call], line)


def assignment(line):
    """

    @param line:
    @return: @rtype:
    """
    line = line.strip()
    if "memory.set" in line:
        return True

    if "==" not in line and line.count("= ") is 1 and not is_member_var(line):
        if not some_func(line):
            return True
    return False


def elif_switch(line):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip() == "":
        return True
    if in_test(["elif", "else"], line):
        return True
    return False


def keyword(line):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip() == "":
        return True
    kws = ["class", "print", "with", "require", "#noinspection", "except", "pass", "del", "return", "with", "super", "catch", " pass", "switch", "raise", "for", "when", "if", "elif", "else", "while", "finally", "try", "unless", "catch"]
    kws = [x+" " for x in kws]
    kws.extend(["$on", "$(", '"""'])
    if in_test(kws, line):
        return True
    elif some_func(line):
        return True
        #elif anon_func(line):
    #    return True
    return False


def indentation(line):
    """

    @param line:
    @return: @rtype:
    """
    cnt = 0
    for c in line:
        if c != " ":
            break
        cnt += 1
    return float(cnt) / 4


def data_assignment(line, prev_line):
    """

    @param line:
    @param prev_line:
    @return: @rtype:
    """
    lvalue = "-"
    if '["' in line and '"]' in line:
        line = line.replace('["', ".")
        prev_line = prev_line.replace('["', ".")
    if "." in line:
        lvalue = line.split(".")[0].strip()
    if "." in prev_line:
        rvalue = prev_line.split(".")[0].strip()
        return lvalue in rvalue
    else:
        return False


def comment(line):
    """

    @param line:
    @return: @rtype:
    """
    if not line:
        return False

    line = line.strip().replace("# ##^", "")
    if line.startswith("#") and "noinspection" not in line:
        return True
    else:
        return False


def whitespace(line):
    """

    @param line:
    @return: @rtype:
    """
    cnt = 0
    for i in line:
        if i != " ":
            return cnt
        cnt += 1
    return cnt


def scope_diff(line, prev_line):
    """

    @param line:
    @param prev_line:
    @return: @rtype:
    """
    if not prev_line:
        return 0

    lws = whitespace(line)
    pws = whitespace(prev_line)
    dif = (pws - lws) / 4

    return dif


def in_test(items, line, return_val=False, words=False):
    """

    @param words:
    @param items:
    @type items:
    @param line:
    @type line:
    @param return_val:
    @type return_val:
    @return: @rtype:
    """
    for item in items:
        if item == line:
            if return_val:
                return item
            return True
        if not words:
            if item in line:
                if return_val:
                    return item
                return True
    if return_val:
        return ""
    return False


def start_in_test(items, line):
    """

    @param items:
    @param line:
    @return: @rtype:
    """
    line = line.strip()
    for item in items:
        if line.startswith(item):
            return True
    return False


def in_test_kw(items, line):
    """

    @param items:
    @param line:
    @return: @rtype:
    """
    items = [x + " " for x in items]
    return in_test(items, line)


def in_test_result(items, line):
    """

    @param items:
    @param line:
    @return: @rtype:
    """
    for item in items:
        if item in line:
            return item.replace('"""', '')
    return None


def is_test(items, line):
    """

    @param items:
    @param line:
    @return: @rtype:
    """
    for item in items:
        if item is line.strip():
            return True
    return False


def is_member_var(line):
    """

    @param line:
    @return: @rtype:
    """
    line = str(line)
    if not "[" in line and not "]" in line and not "= {" in line and not "@param" in line and (":" in line and not ".cf" in line) and (line.count(":") is 1 and not '":"' in line and not "':'" in line) and not anon_func(line) and not in_test(["warning"], line) and not keyword(line):
        return True
    return False


def global_line(line):
    """

    @param line:
    @return: @rtype:
    """
    return line.find(" ") != 0


def global_object_method_call(line):
    """

    @param line:
    @return: @rtype:
    """
    if global_line(line):
        if "." in line and parenthesis(line):
            return True
    return False


def class_method_call(line):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip().find("@") == 0:
        if "(" in line and ")" in line:
            return True
    return False


def function_call(line):
    """

    @param line:
    @return: @rtype:
    """
    if parenthesis(line) and not "." in line:
        return True
    return False


def double_meth_call(line):
    """

    @param line:
    @return: @rtype:
    """
    if "serverconfig" in line:
        return False
    return "self" in line and line.count("()") > 1


def coffee_script_pretty_printer(add_double_enter, add_enter, debuginfo, first_method_class, first_method_factory, line, next_line, prev_line, resolve_func, scoped, if_cnt, in_python_comment, fname):
    """


    @param fname:
    @param add_double_enter:
    @param add_enter:
    @param debuginfo:
    @param first_method_class:
    @param first_method_factory:
    @param line:
    @param next_line:
    @param prev_line:
    @param resolve_func:
    @param scoped:
    @param if_cnt:
    @param in_python_comment:
    @return: @rtype:
    """
    add_docstring = False
    line_redone = org_line = line

    if scoped > 0:
        if if_cnt > 0:
            if_cnt -= scoped

    if line.strip().startswith("if"):
        if_cnt += 1

    if ".factory" in line:
        add_double_enter = True
        debuginfo = ".factory"

    if line.startswith("class"):
        if "noinspection" in prev_line:
            debuginfo = "class def after inspection"
        else:
            add_double_enter = True
            debuginfo = "class def"
    elif line.strip().startswith("@") and not (line.strip().startswith("@m_") and ".setter" not in line) and not '"""' in prev_line and not "param" in line and fname.endswith(".py"):
        debuginfo = "property "
        if func_def(prev_line):
            debuginfo += " after func"
        else:
            if line.find(" ") > 0 or line.find(" ") == -1:
                debuginfo += " global"
                add_double_enter = True
            else:
                add_enter = True

    elif "#noinspection" in line:
        debuginfo = "pycharm directive"
        if not keyword(prev_line) or "return" in prev_line or "raise" in prev_line:
            add_enter = True
        else:
            add_enter = False
            debuginfo += " after keyword"
        if next_line:
            if keyword(next_line) and not keyword(prev_line):
                if "class" not in next_line:
                    debuginfo += " keyword (not class) in nextline"
                    add_enter = True
                    add_double_enter = False
        if next_line.rstrip().startswith("def "):
            add_double_enter = True
        if next_line.rstrip().startswith("class "):
            add_double_enter = True

    elif prev_line.strip().startswith("raise"):
        debuginfo = "raise"
        if "except" not in line and "else" not in line:
            debuginfo = " after raise"
            add_enter = True
            if func_def(line) and not "(self" in line:
                add_double_enter = True

    elif "break" == prev_line.strip():
        debuginfo = "break"
        add_enter = True
    elif "return" in line:
        debuginfo = "retrn"
        if not comment(line) and not comment(prev_line):
            add_enter = False

            if whitespace(prev_line) - whitespace(line) > 0:
                add_enter = True
                debuginfo = " whitespace"
            if '"""' in prev_line:
                add_enter = False
                debuginfo = " after doc comment"
            elif keyword(prev_line):
                add_enter = False
                debuginfo = " after keyword"
            elif func_def(prev_line):
                add_enter = False
                debuginfo += " after funcdef"
            elif prev_line:
                debuginfo += " | "

                if next_line:
                    if (prev_line.strip() == "") or ("else" in prev_line) or ("else" in next_line) and not in_test(["setInterval", "setTimeout"], prev_line):
                        debuginfo += " after empty line time func or 3lse"
                elif is_test([")"], prev_line.strip()) or in_test(["_.filter", "_.map"], prev_line):
                    debuginfo += " after close or underscore func"
                    #add_enter = True
                elif "return" in prev_line:
                    debuginfo += " after rturn"
                    #add_enter = True
                elif keyword(prev_line):
                    debuginfo += "after keyword"
                    add_enter = False
                else:
                    if next_line and not in_test(["setInterval", "setTimeout"], prev_line):
                        if "class" not in next_line or len(str(next_line)) > 0:
                            debuginfo += " after js time func"
                    elif scoped > 1:
                        debuginfo += " after scope d!ff " + str(scoped)
                        #add_enter = True

    elif "__main__'" in line:
        add_double_enter = True
        debuginfo = "main"
    elif line.strip().startswith("class"):
        add_enter = True
        debuginfo = "class def"
    elif "unless" in line:
        add_enter = True
        debuginfo = "unless"
    elif double_meth_call(line):
        debuginfo = "double method call"
        if not keyword(prev_line):
            if not double_meth_call(prev_line):
                add_enter = True
    elif global_class_declare(line):
        debuginfo = "global_class_declare"
        add_enter = True
    elif line.strip().startswith("try"):
        debuginfo = "try"
        if not keyword(prev_line) and not prev_line.strip() == '"""' and not resolve_func:
            add_enter = True
    elif assignment(line):
        debuginfo = "assignment"
        global datastructure_define
        if "[" in line and not "]" in line and not "\\033[" in line:
            debuginfo += " datastructure"
            datastructure_define = True
        else:
            debuginfo = "assignment"
        if scoped > 0:
            debuginfo += " prev scope"
            add_enter = True

        if global_line(line):
            debuginfo += " on global"
            if not global_line(prev_line):
                add_double_enter = True
        if scoped > 1:
            debuginfo += " on prev scope"
            add_enter = True
        elif on_scope(line):
            debuginfo += " on scope"
        if scoped >= 2:
            add_enter = True
            debuginfo += " new scope"

    elif global_object_method_call(line):
        debuginfo = "global method call"
        if "#noinspection" not in prev_line and "import " not in prev_line:
            add_double_enter = True
    if ": [" in line and not fname.endswith(".py"):
        debuginfo = "struct coffeescript"
        add_enter = True
    elif class_method(line):
        debuginfo = "class_method"
        if first_method_class:
            debuginfo += " " + str(first_method_class)

            if "class" in prev_line:
                add_enter = False
            else:
                add_enter = True
        elif first_method_factory:
            debuginfo = "factorymethod " + str(first_method_factory)

            add_enter = True
        else:
            debuginfo = "method"
            if is_member_var(prev_line):
                debuginfo += " after member var"
                add_enter = True
            else:
                if scoped < 0:
                    if "unless" not in prev_line:
                        add_enter = True
                        debuginfo += " in a nested scope" + str(global_class_declare(prev_line))
                    else:
                        debuginfo += " in a nested scope after unless"

                    if global_class_declare(prev_line):
                        debuginfo += " after class declare"
                        add_enter = False
                else:
                    if indentation(line) == 1:
                        debuginfo += " indented 1"
                        if scoped >= 1:
                            debuginfo += " scoped >=1"
                            add_double_enter = True
                        else:
                            add_enter = True
                    else:
                        add_enter = True
    elif line.strip().find("warning") == 0 and ":" not in line and ">" not in line:
        debuginfo = "error state (wrning)"
    elif "it " in line and ("->" in line or "=>" in line):
        debuginfo = "karma test"
        add_enter = True
    elif "@unittest" in line:
        add_enter = True
        debuginfo = "unittest decorator"
    elif ".$on" in line:
        debuginfo = "0n event"
        if scoped == 0:
            debuginfo += " on same scope "
            add_enter = True
        if scoped == 0:
            debuginfo += " on same scope "
            add_enter = True
    elif "set_time_out" in line:
        debuginfo = "set_time_out"
        if not func_def(prev_line) and not start_in_test(["if", "else"], prev_line):
            add_enter = True
    elif line.strip().find("it ") == 0:
        debuginfo = "test statement"
        if not some_func(prev_line) and not anon_func(prev_line):
            add_enter = True
    elif line.strip().find("describe ") == 0:
        debuginfo = "describe statement"
        if not some_func(prev_line) and not anon_func(prev_line):
            add_enter = True
    elif "$observe" in line and "$observe" not in prev_line:
        debuginfo = "observe method"
        add_enter = True
    elif ".then" in line:
        debuginfo = "resolve method body"
        resolve_func += 1
        if prev_line:
            if not in_test(["if", "else", "->", "=>"], prev_line):
                add_enter = True
    elif func_def(line):
        if '"""' not in next_line:
            add_docstring = True
        debuginfo = "function def"
        if line.find(" ") is not 0:
            if prev_line.strip().startswith("@"):
                debuginfo += "after property"
            else:
                add_double_enter = True
        else:
            if not func_def(prev_line) or comment(prev_line):
                debuginfo = "function def nested"
                if func_def(prev_line):
                    debuginfo += " after function def"
                    add_enter = False
                elif assignment(prev_line):
                    debuginfo = "function def nested after assignement"
                    add_enter = True
                elif class_method(prev_line):
                    debuginfo += " after method"
                elif "@unittest" in prev_line:
                    debuginfo += " after unittest decorator"
                    add_enter = False
                elif in_test(["if", "else"], prev_line):
                    debuginfo += " after if or else"
                elif keyword(prev_line):
                    debuginfo += " after keyword"
                    add_enter = True
                elif anon_func(prev_line):
                    debuginfo += " after anon func"
                    add_enter = False
                elif not class_method(prev_line) and not keyword(prev_line) and not assignment(prev_line):
                    debuginfo += " somewhere"
                    add_enter = True
                    if "return" in prev_line:
                        add_enter = True
                        debuginfo += " in a class"
                    if scoped > 1:
                        add_enter = True
                        debuginfo = "scope change"
                    if "@" in prev_line or keyword(prev_line):
                        add_enter = False
                        debuginfo += " after property or kw"
                elif first_method_factory:
                    debuginfo += "first method factory"
                    add_enter = True
                elif on_scope(line):
                    debuginfo += " on scope"
                    add_enter = True
                elif scoped > 0:
                    debuginfo += " on previous scope"
                    add_enter = True
                if "(self" in line and not "class" in prev_line and not '"""' in prev_line and not prev_line.strip().startswith("@"):
                    debuginfo += " a python class "
                    add_double_enter = False
                    if "#@" in prev_line or "# @" in prev_line:
                        debuginfo += " after commented out property"
                        add_enter = False
                    else:
                        add_enter = True
                    if "noinspection" in prev_line:
                        debuginfo += " after no inspection"
                        add_enter = False
                if "(self" in line and ("class" in prev_line or '"""' in prev_line) and not prev_line.strip().startswith("@"):
                    debuginfo += " first method"
                    add_double_enter = False
                    add_enter = True

            else:
                debuginfo = "functiondef after functiondef"
        if line.strip().startswith("def "):
            if not "(self" in line and not "(cls" in line and not "@" in prev_line and not prev_line.strip().startswith("def ") and not line.startswith(" ") and not "#noinspection" in prev_line:
                add_enter = True
                add_double_enter = True
                debuginfo += " python"
            elif "noinspection" in prev_line:
                add_enter = False
                add_double_enter = False
                debuginfo += " after noinspection"

    elif class_method_call(line) and not fname.endswith(".py"):
        debuginfo = "class method call"
        if scoped > 1:
            add_enter = True
            debuginfo += " scoped"
    elif scoped_method_call(line):
        debuginfo = "scoped_method_call"
        if prev_line:
            if not func_test([method_call, class_method], prev_line.strip()) and not in_test([".then", "if", "->", "=>", "else"], prev_line):
                debuginfo += " method define or scoped method call"
                if line.find(" ") is not 0:
                    if len(prev_line) > 0:
                        add_double_enter = True
                    else:
                        debuginfo += "after non empty line"
                        add_enter = True
                else:
                    debuginfo += " not on globalscope"
    elif anon_func(line) and not in_test([".directive", "$watch", ".bind"], line):
        debuginfo = "anonymousfunction"
        if not resolve_func:
            if line.count("    ") is 1 and not assignment(prev_line) and not func_def(prev_line):
                debuginfo = "anonymousfunction2"
                add_enter = True
            if line.find(" ") is not 0:
                add_double_enter = True
        else:
            debuginfo = "resolve result 2"
    elif line.strip().startswith("super("):
        debuginfo = "super"
        if scoped > 0:
            debuginfo = " with scope chage"
            add_enter = True
    elif "if" in line and (line.strip().find("if") is 0 or line.strip().find("else") is 0):
        debuginfo = " if statement"

        if scoped > 0:
            debuginfo += " scope change"
            add_enter = True

        if scoped == 0:
            debuginfo += " on same scope"
            if "_.defer" in prev_line:
                debuginfo += " after defer call"
                add_enter = True

            if assignment(prev_line):
                debuginfo += " after assignement"
                add_enter = True
            if "if" in prev_line:
                debuginfo += " after if"
                add_enter = True
            if method_call(prev_line):
                debuginfo += " after method call"
                add_enter = True

        if "else" in line:
            debuginfo += " else"
            add_enter = False
    elif in_test_kw(["when"], line):
        debuginfo = in_test_result(["when"], line) + " statement"
    elif "pass" == prev_line.strip() and not in_test_result(["if", "elif", "else"], line):
        debuginfo = " pass"
        add_enter = True
    elif in_test_kw(["switch", "for", "while"], line) and not in_test_kw(["switch", "for", "while"], prev_line) and not comment(prev_line):
        debuginfo = in_test_result(["switch", "try", "when", "while", "if", "for"], line) + " statement"
        if prev_line:
            if not in_test(["when", "if", "->", "=>", '"""', "def ", "else", "with", "switch", "try", "#noinspection"], prev_line):
                if in_test(["return"], prev_line) and in_test(["when"], line) and scoped > 1:
                    debuginfo += " prevented when statement"
                else:
                    add_enter = True
            else:
                debuginfo += " prevented by " + str(in_test_result(["when", "if", "->", "=>", "else", "switch"], prev_line))
    elif line.strip().startswith(".directive"):
        add_enter = True
        debuginfo = ".directive "
    elif is_member_var(line) and not fname.endswith(".py"):
        debuginfo = "is_member_var "
        ls = line.strip().split(" ")
        first_word = ""
        if ls > 0:
            first_word = ls[0]
        if not keyword(first_word):
            debuginfo += " member initialization"
            if scoped > 0:
                if not is_member_var(prev_line):
                    add_enter = True
                    debuginfo += " new scope"
    elif method_call(line):
        debuginfo = "methodcall"
        if assignment(line):
            debuginfo += " and assigned "
        if line.find(" ") is not 0:
            debuginfo += "method call global scope"
            if "# noins" not in prev_line and "import " not in prev_line:
                add_enter = False
                add_double_enter = True
            if ")()" in line.strip():
                debuginfo += " end mod"
                add_enter = False
                add_double_enter = False
        elif prev_line:
            if method_call(prev_line):
                if whitespace(line) < whitespace(prev_line):
                    if not elif_switch(prev_line):
                        debuginfo += " method call higher scope " + str(whitespace(prev_line) - whitespace(line))
                        if whitespace(prev_line) - whitespace(line) > 0:
                            add_enter = True
                            debuginfo += " scope>2 "
                else:
                    debuginfo += "nested method call"
            elif not func_test([func_def, scoped_method_call, method_call, class_method], prev_line.strip()):
                if data_assignment(line, prev_line):
                    debuginfo += "method call data assignment " + str(if_cnt)
                    add_enter = False
                else:
                    if assignment(prev_line):
                        if scoped == 0:
                            add_enter = False
                            debuginfo += " after assignment"
                        else:
                            add_enter = True
                            debuginfo += " scope change"
                    else:
                        test_items = ["@staticmethod", "catch", "print", "with", "when", "_.keys", "finally", "except", '"""', "->", "=>"]
                        if in_test(test_items, prev_line):
                            debuginfo += " after " + str(in_test_result(test_items, prev_line)).replace("print", "pr1nt")
                        else:
                            if comment(prev_line):
                                debuginfo += " after comment"
                            else:
                                debuginfo += " not after comment"
                                add_enter = True
                                if assignment(line):
                                    debuginfo += " and assigned "
                                    add_enter = False
                if in_test(["$watch", "if", "else", "for", "while", "try:", "#noinspection"], prev_line.strip()):
                    debuginfo += "method call after 1f 3lse or wtch"
                    add_enter = False
                    add_double_enter = False
            else:
                debuginfo += "method call nested "
                add_enter = False
    elif line.strip().startswith("raise"):
        debuginfo = " raise"
        if not in_test(["if", "else", "except"], prev_line):
            debuginfo += " after if"
            add_enter = False
        elif not method_call(prev_line):
            debuginfo += " after methodcall"
            add_enter = False
        elif prev_line.strip().startswith("console"):
            debuginfo += " after console statement"
            add_enter = False
            add_double_enter = False
    elif function_call(line):
        debuginfo = "function call"
        if not function_call(prev_line):
            if "return" in prev_line and not "_return" in prev_line:
                debuginfo = " after return"
                add_enter = True
        if prev_line.strip() == ")":
            debuginfo = " new line"
            add_enter = True
    elif start_in_test(["class"], line):
        debuginfo = "class"
        add_double_enter = True
    elif "except" in line:
        debuginfo = "except"
        #add_enter = True
    elif line.lstrip().startswith("$scope") and in_test(["->", "=>"], line):
        debuginfo = "scoped method define"
        if prev_line:
            if not ")" is prev_line.strip():
                add_enter = True
    elif "$(e" in line:
        debuginfo = "jquery"
        if not keyword(prev_line):
            add_enter = True
    elif "$watch" in line:
        debuginfo = "watch def"
        if not keyword(prev_line):
            if scoped == 0:
                add_enter = True
    elif "raise" in line:
        if not keyword(prev_line):
            debuginfo = "raise"
            add_enter = True
    elif "try" in line:
        debuginfo = "try"
    elif "angular.module" in line:
        debuginfo = "angular module"
        add_double_enter = True
    elif "$." in line:
        if prev_line:
            if not ("_." in prev_line or "$." in prev_line or "if" in prev_line):
                if not resolve_func:
                    add_enter = True
                    debuginfo = ".each"
    elif line.lstrip().startswith("f_") and (line.endswith("->") or line.endswith("=>")):
        add_double_enter = True
    elif "setInterval" in line or "setTimeout" in line:
        debuginfo = "setInterval timeout"
    elif "print" in line:
        debuginfo = "debug statement"
        if "->" in line:
            debuginfo = "func with print"
            add_enter = True
            if class_method(prev_line):
                debuginfo = "func with print after classmethod"
                add_enter = False

    if "{" in line and "}" in line and ":" in line and "," in line and line.strip().endswith("}"):
        nesting = line.find("{")
        if fname.endswith(".py"):
            line_redone = line.replace(",", ",\n" + nesting * " ")

    if line.count('"""') % 2 != 0:
        if in_python_comment:
            in_python_comment = False
        else:
            in_python_comment = True
            if next_line.count('"""') > 0 or "rtype" in next_line:
                if "rtype" in next_line:
                    next_line = ""
                if "(" in prev_line:
                    emptydocstring = prev_line.replace("def ", "").replace("class ", "").strip()
                    if "(" in emptydocstring:
                        emptydocstring = emptydocstring.split("(")[0]
                    docstring = ""

                    if ")" in prev_line:
                        pls = prev_line.split("(")[1].split(")")[0].split(",")
                        pls = [x.strip() for x in pls if len(x) > 0]
                        empty = True
                        for typeitem in pls:
                            if typeitem != "self" and typeitem != "Exception" and typeitem != "object" and "admin." not in typeitem.lower() and "model." not in typeitem.lower():
                                empty = False
                                mytype = "str"
                                typeval = None
                                if "=" in typeitem:
                                    tis = typeitem.split("=")
                                    typeitem = tis[0]
                                    typeval = tis[1].strip()

                                if typeitem.startswith("i_"):
                                    mytype = "int"
                                elif "size" in typeitem:
                                    mytype = "int"
                                elif "index" in typeitem:
                                    mytype = "int"
                                elif "cnt" in typeitem:
                                    mytype = "int"
                                elif "dict" in typeitem:
                                    mytype = "dict"
                                elif "list" in typeitem:
                                    mytype = "list"
                                elif "ids" in typeitem:
                                    mytype = "list"
                                elif typeitem.startswith("d_"):
                                    mytype = "dict"
                                elif typeitem.startswith("l_"):
                                    mytype = "list"
                                elif typeitem.startswith("f_"):
                                    mytype = "float"
                                elif typeitem.startswith("u_"):
                                    mytype = "unicode"
                                elif typeitem.startswith("s_"):
                                    mytype = "str"
                                elif typeitem.startswith("b_"):
                                    mytype = "bool"
                                elif typeitem.startswith("request"):
                                    mytype = "HttpRequest, django.core.handlers.wsgi.WSGIRequest"
                                elif typeitem.startswith("serverconfig"):
                                    mytype = "ServerConfig"
                                elif typeitem.startswith("dbase"):
                                    mytype = "CouchDBServer"

                                elif typeitem == "cryptobox":
                                    mytype = "CryptoboxDB"
                                elif typeitem == "cryptobox_db":
                                    mytype = "CryptoboxDB"
                                elif typeitem == "login_token":
                                    mytype = "LoginToken"

                                if typeval:
                                    if typeval == "True" or typeval == "False":
                                        mytype = "bool"
                                    elif typeval == "None" or typeval == "None":
                                        mytype += ", None"
                                    elif '"' in typeval or "'" in typeval:
                                        mytype = "str"
                                    else:
                                        try:
                                            if "." in str(typeval):
                                                float(typeval)
                                            mytype = "float"
                                        except:
                                            pass
                                        try:
                                            int(typeval)
                                            mytype = "int"
                                        except:
                                            pass
                                if "kwargs" in typeitem or "args" in typeitem:
                                    if "kwargs" in typeitem:
                                        typeitem = "@param kwargs:"
                                    elif "args" in typeitem:
                                        typeitem = "@param args:"
                                else:
                                    typeitem = "@type " + typeitem + ": " + mytype
                                docstring += next_line.count(" ") * " " + typeitem + "\n"

                        if empty:
                            line_redone += "\n" + line.replace('"""', "") + emptydocstring.strip()
                        else:
                            line_redone += "\n" + line.replace('"""', "") + docstring.strip()

    if "]" in line and not "[]" in line:
        if datastructure_define:
            debuginfo += " end datastructure_define"
        datastructure_define = False

    if datastructure_define:
        debuginfo += " in datastructure_define"
        add_double_enter = False
        add_enter = False
    if in_python_comment:
        debuginfo += " in in_python_comment"
        add_double_enter = False
        add_enter = False
        if line.strip().startswith("@param") and "args" not in line:
            if not next_line.strip().startswith("@type"):
                line_redone += "\n" + org_line.split("@param")[0] + "@type " + line.strip().split("@param")[1].split(":")[0].strip() + ": "
    if add_docstring and fname.endswith(".py") and not in_python_comment:

        line_redone += "\n"
        line_redone += " " * (whitespace(line)+4)
        line_redone += '"""\n'
        line_redone += " " * (whitespace(line)+4)
        line_redone += '"""\n'

    debuginfo = debuginfo.replace("  ", " ")
    return in_python_comment, add_double_enter, add_enter, debuginfo, resolve_func, if_cnt, line_redone


def coffeescript_pretty_printer_emitter(add_double_enter, add_enter, cnt, line, mylines, prev_line):
    #print debuginfo, add_enter, add_double_enter
    """

    @param add_double_enter:
    @param add_enter:
    @param cnt:
    @param line:
    @param mylines:
    @param prev_line:
    @return: @rtype:
    """
    global datastructure_define

    if add_double_enter:
        cont = True
        #if cnt - 1 > 0:
        #    if ".module" in prev_line:
        #        cont = False


        if cont:
            if cnt - 1 > 0:
                if not len(prev_line.strip()) is 0:
                    line = "\n" + line
            if cnt - 2 > 0:
                if not len(mylines[cnt - 2].strip()) is 0:
                    line = "\n" + line
    if add_enter:
        if cnt - 1 > 0:
            if not len(prev_line.strip()) is 0:
                line = "\n" + line
    return line


def add_debuginfo(debuginfo, line):
    """

    @param debuginfo:
    @param line:
    @return: @rtype:
    """
    if debuginfo:
        ef = line.find("\n")
        if ef > 0 and ef is not 0:
            line = line.rstrip("\n")
        line = line + " # ##^ " + debuginfo.replace("i", "1").replace("return", "retrn")
        if ef > 0 and ef is not 0:
            line += "\n"
        debuginfo = ""

    return debuginfo, line


def sanatize_line(line, next_line):
    """

    @param line:
    @param next_line:
    @return: @rtype:
    """
    if not (line.strip().endswith(",") or ")" in next_line) and not in_test([")", "=>", "!=", "==", "$(", "?", "ng-", "trim", "strip", "match", "split", "input", "type=", "/=", "\=", ":", "replace", "element", "if ", "b64", "padding"], line):
        line = line.replace("=>", "@>").replace("( ", "(").replace("=", " = ").replace("  =", " =").replace("=  ", "= ").replace("@>", "=>").replace("< =", "<=").replace("> =", ">=").replace("+ =", "+=").replace("- =", "-=").replace("* =", "*=").replace("! =", "!=").replace('(" = ")', '("=")').replace('+ " = "', '+ "="')
        if not "+=" in line and not "++" in line:
            line = line.replace("+", " + ")
            line = line.replace("  +  ", " + ")
    for i in range(0, 10):
        line = line.replace("( ", "(")
        line = line.replace("  =", " =")
        line = line.replace("  is  ", " is ")
        line = line.replace("  is not  ", " is ")
    line = line.replace("coding = utf-8", "coding=utf-8")
    line += "\n"
    return line


def coffeescript_pretty_print_resolve_function(add_enter, debuginfo, line, prev_line, resolve_func):
    """

    @param add_enter:
    @param debuginfo:
    @param line:
    @param prev_line:
    @param resolve_func:
    @return: @rtype:
    """
    if resolve_func:
        if anon_func(line) and in_test(["(", ")"], line) and not "= " in line:
            if resolve_func:
                if prev_line:
                    if not (".then" in prev_line or "->" in prev_line or "=>" in prev_line):
                        add_enter = True
                        debuginfo = "resolve func"

        if line.strip() is ")":
            debuginfo = "resolve func stopped"
            resolve_func -= 1
    return add_enter, debuginfo, resolve_func

#noinspection PyUnusedLocal
def add_file_and_linenumbers_for_replace_vars(args, fname, line, location_id, orgfname, undo_variables, variables):
    """

    @param args:
    @param fname:
    @param line:
    @param location_id:
    @param orgfname:
    @param undo_variables:
    @param variables:
    @return: @rtype:
    """
    for replace_variable in variables:
        #if "print_once" in line:
        #    line = line.replace("print_once(", "print_once (")
        check_split = line.split(" ")
        check_split2 = []
        for i in check_split:
            check_split2.extend(i.split("("))

        check_split = [x.strip() for x in check_split2]

        found_color = False
        if replace_variable in check_split and len(line.strip()) > 0:
            if replace_variable + " = " not in line:
                if fname.endswith(".py"):
                    if "93m" in line:
                        found_color = True
                        line = line.replace('"\\033[93m" + log_date_time_string(),', "")
                        line = line.replace('"\\033[93m"', "")
                        line = line.replace('93m', "")
                        line = line.replace('log_date_time_string(),', "")
                        line = line.replace(", '\\033[m'", "")
                    else:
                        line = line.replace('log_date_time_string(),', "")
                if fname in line:
                    line2 = line.replace(fname, "")
                    lines = line2.split(",")

                    def lnr(code_line):
                        """ lnr
                        @param code_line:
                        """
                        if ":" not in code_line:
                            return code_line

                    lines = [i.strip() for i in lines if lnr(i)]
                    line = line2.split(replace_variable)[0]
                    line += replace_variable + " "
                    for linet in lines:
                        line += linet
                        line += ", "

                if replace_variable + "(msg" not in line and "do " not in line:
                    line = line.replace(replace_variable + "(", replace_variable)
                    location = fname + ":" + "@@@@"
                    location_id += 1

                    if replace_variable not in undo_variables:
                        line = line.replace(replace_variable, replace_variable + "(\"" + str(location) + "\",")
                    else:
                        line = line.replace(replace_variable, replace_variable + "(").replace("( \"", "(\"")
                for i in range(0, 20):
                    line = line.rstrip(",")
                    line = line.rstrip()
                question = False
                if "?" in line:
                    question = True
                    line = line.replace("?", "")
                if ".then" not in line:
                    line = line.rstrip(")")
                    if line.count("(") != line.count(")"):
                        for i in range(0, line.count("(") - line.count(")")):
                            line += ")"
                if question:
                    line += "?"

                if orgfname.endswith(".py"):
                    if found_color:
                        line = line.replace("print(", "print \"\\033[93m\" + log_date_time_string(), ")
                    else:
                        line = line.replace("print(", "print ")
                    if line.strip().startswith("print"):
                        line = line.replace("print(", "print ")
                        line = line[:len(line) - 1]
                else:
                    if "print(" in line:
                        line = line.replace("print(", "print ")
                        line = line[:len(line) - 1]
                    for i in range(0, 5):
                        line = line.replace("print  ", "print ")
                    if "warning(" in line:
                        line = line.replace("warning(", "warning ")
                        line = line[:len(line) - 1]
                    if "print_once(" in line:
                        line = line.replace("print_once(", "print_once ")
                        line = line[:len(line) - 1]

                if found_color:
                    line += ", '\\033[m'"

                line += "\n"
                line = line.replace('",', '", ')
                line = line.replace('",  ', '", ')

                if replace_variable == "throw":
                    line = line.replace(",", " +")

    return line


def arg_parse():
    """


    @return: @rtype:
    """
    parser = ArgumentParser()
    parser.add_argument("-f", dest="myfile")
    parser.add_argument("-r", dest="release")
    args = parser.parse_args()
    return args


def init_file(args):
    """

    @param args:
    @return: @rtype:
    """
    myfile = None
    if args.myfile:
        myfile = open(args.myfile)
        content = ""
        for i in myfile:
            if str(i).strip() != "":
                content += i
        open(args.myfile, "w").write(content)
        myfile = open(args.myfile)
    else:
        print "no -f (file) given as argument"
        exit(1)
    buffer_string = ""
    num = 1
    orgfname = fname = os.path.basename(args.myfile)
    if "__init__" in fname:
        fname = "/".join(str(args.myfile).split("/")[-2:])
        if "__init__" in fname:
            fname = os.path.basename(os.getcwd())
            fname = fname+"/"+(str(orgfname))

        #fname = fname.replace("__init__.py", "")
        #fname = fname.replace("/:", ":")
    return buffer_string, fname, myfile, num, orgfname

#noinspection PyPep8Naming
def init_cp(args, fname, myfile):
    """

    @param args:
    @param fname:
    @param myfile:
    @return: @rtype:
    """
    color_vals_to_keep, undo_variables, variables, watch_vars = replace_variables()
    mylines = []
    fname = fname.replace("coffee", "cf")
    import cStringIO
    data = myfile.read()
    if "ADDTYPES" in data or "addtypes" in data:
        global ADDCOMMENT_WITH_FOUND_TYPE
        ADDCOMMENT_WITH_FOUND_TYPE = True
    for i in range(0, 10):
        data = data.replace("\n\n", "\n")
    data = data.replace(")->", ") ->")
    data = data.replace(")=>", ") =>")
    for line in data.split("\n"):
        mylines.append(line + "\n")
    cnt = 0
    location_id = 0

    if ".cf" not in fname and ".py" not in fname:
        myfile.close()
        mylines = open(args.myfile)
        #mylines = cStringIO.StringIO(data)
    resolve_func = 0
    debuginfo = ""
    in_if = False
    first_method_factory = first_method_class = False
    return cStringIO, cnt, color_vals_to_keep, debuginfo, first_method_class, first_method_factory, fname, in_if, location_id, mylines, resolve_func, undo_variables, variables, watch_vars


def prepare_line(cnt, line, mylines):
    """

    @param cnt:
    @param line:
    @param mylines:
    @return: @rtype:
    """
    prev_line = ""
    next_line = None
    if cnt > 1:
        prev_line = mylines[cnt - 1]
    if len(mylines) > cnt + 1:
        next_line = mylines[cnt + 1]
    scoped = scope_diff(line, prev_line)
    ls = line.split("# ##^ ")
    ltemp = ls[0].rstrip()
    if ADDCOMMENT_WITH_FOUND_TYPE:
        if ltemp.strip() == "" and len(ls) > 0:
            ltemp = line
    line = ltemp
    line = line.replace("\n", "")
    add_enter = add_double_enter = False

    #line = line.replace("console.log ", "console?.log? ")
    #line = line.replace("console?.log", "console?.log")
    #line = line.replace("console?.log?", "print")
    line = line.replace("# noinspection", "#noinspection")
    line = line.replace("console?.error?", "warning")
    line = line.replace("console?.error", "warning")
    #line = line.replace("console.log", "print")

    return add_double_enter, add_enter, line, next_line, prev_line, scoped


def exceptions_coffeescript_pretty_printer(add_double_enter, add_enter, cnt, debuginfo, line, next_line, prev_line, scoped, if_cnt):
    """


    @param prev_line:
    @param add_double_enter:
    @param add_enter:
    @param cnt:
    @param debuginfo:
    @param line:
    @param next_line:
    @param scoped:
    @param if_cnt:
    @return: @rtype:
    """
    if comment(line):
        if debuginfo:
            debuginfo = "comment -> " + debuginfo
        else:
            debuginfo = "comment"
        if not comment(prev_line) and not "else" in prev_line and not func_def(prev_line) and not anon_func(prev_line) and not prev_line.strip().startswith("if "):
            add_enter = False
            add_double_enter = False
            debuginfo = " comment after something"
        if line.find(" ") > 0:
            add_double_enter = True
    if add_double_enter:
        add_enter = False

    elif cnt > 1:
        if line.strip() != "":
            if scoped >= 3:
                if not class_method(line):
                    if not add_double_enter:
                        debuginfo += "triple scope change"
                        add_enter = True
                    if next_line:
                        if "else" not in line:
                            debuginfo += " scope level "
                            add_enter = True
                    if len(line.strip()) <= 2:
                        add_enter = False
                        debuginfo += " some closing tag"

    debuginfo += " " + str(if_cnt) + str(add_double_enter)
    return add_double_enter, add_enter, debuginfo, line

#noinspection PyPep8Naming
def main(args):
    """
        main function
    @param args:
    """
    if args.myfile == "cp.py":
        return

    print "cp.py -f", os.path.basename(os.path.dirname(args.myfile)) + "/" + os.path.basename(args.myfile)

    buffer_string, fname, myfile, num, orgfname = init_file(args)

    cStringIO, cnt, color_vals_to_keep, debuginfo, first_method_class, first_method_factory, fname, in_if, location_id, mylines, resolve_func, undo_variables, variables, watch_vars = init_cp(args, fname, myfile)

    line_cnt = 0
    if_cnt = 0
    in_python_comment = False
    for line in mylines:
        line_cnt += 1
        for v in watch_vars:
            if v.lower() in line.lower():
                print line

        process_line = True

        if "console" in line:
            for i in range(0, line.count("if running_local()")):
                line = line.replace("if running_local()", "")
            line = line.replace("log?  ", "log? ")

        add_double_enter, add_enter, line, next_line, prev_line, scoped = prepare_line(cnt, line, mylines)

        in_python_comment, add_double_enter, add_enter, debuginfo, resolve_func, if_cnt, line = coffee_script_pretty_printer(add_double_enter, add_enter, debuginfo, first_method_class, first_method_factory, line, next_line, prev_line, resolve_func, scoped, if_cnt, in_python_comment, fname)

        add_double_enter, add_enter, debuginfo, line = exceptions_coffeescript_pretty_printer(add_double_enter, add_enter, cnt, debuginfo, line, next_line, prev_line, scoped, if_cnt)

        add_enter, debuginfo, resolve_func = coffeescript_pretty_print_resolve_function(add_enter, debuginfo, line, prev_line, resolve_func)

        #if ".cf" in fname:
        line = coffeescript_pretty_printer_emitter(add_double_enter, add_enter, cnt, line, mylines, prev_line)

        if not ADDCOMMENT_WITH_FOUND_TYPE:
            debuginfo = ""

        debuginfo, line = add_debuginfo(debuginfo, line)

        line = sanatize_line(line, str(next_line))

        restore_color = None
        if orgfname.strip().endswith(".py"):
            for color in color_vals_to_keep:
                if color in line:
                    restore_color = color
                    line = line.replace(color, "93m")

        if process_line:
            line = add_file_and_linenumbers_for_replace_vars(args, fname, line, location_id, orgfname, undo_variables, variables)

        if restore_color:
            line = line.replace('93m', restore_color)

        buffer_string += line
        num += 1
        cnt += 1

    myfile.close()

    sio_file2 = cStringIO.StringIO("\n" + buffer_string.lstrip())
    #open(args.myfile, "w").write()

    num = 0
    if str(args.myfile).endswith(".coffee"):
        num += 1

    buffer_string = ""
    for line in sio_file2:
        line = line.replace("@@@@", str(num))
        num += 1
        if line.strip() != "#":
            buffer_string += line

    if str(args.myfile).endswith(".coffee"):
        finalbuf = "\n" + buffer_string.strip() + "\n"
        open(args.myfile, "w").write(finalbuf)
    else:
        open(args.myfile, "w").write(buffer_string.strip() + "\n")



def lock_acquire(key):
    """

    @param key:
    """
    lfile = key + ".lock"
    cnt = 0

    while os.path.exists(lfile):
        time.sleep(0.1)
        cnt += 1
        if cnt > 200:
            os.remove(lfile)
    open(lfile, "w").write("x")


def lock_release(key):
    """

    @param key:
    @return: @rtype:
    """
    lfile = key + ".lock"
    if os.path.exists(lfile):
        # noinspection PyBroadException
        try:
            os.remove(lfile)
        except:
            pass
        return True
    return True


if __name__ == "__main__":
    args = arg_parse()
    lock = os.path.dirname(os.path.join(os.getcwd(), args.myfile))+"/cp"
    try:
        lock_acquire(lock)
        main(args)
    finally:
        lock_release(lock)
