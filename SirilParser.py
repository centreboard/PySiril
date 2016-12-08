import re
from CompositionClasses import PlaceNotationPerm, Row
from Exceptions import SirilError, StopRepeat
import SirilProver


def full_parse(line, assignments_dict, stage, index):
    line, assignments_dict, index = string_parsing(line, assignments_dict, index)
    line, assignments_dict, index = bracket_parsing(line, assignments_dict, stage, index)
    out, assignments_dict, index = argument_parsing(line, assignments_dict, stage, index)
    return out, assignments_dict, index


def string_parsing(line, assignments_dict, index):
    line = line.replace("'", "\"")
    while "\"" in line:
        left, _, right = line.partition("\"")
        if "\"" not in right:
            raise SirilError("String not closed", line)
        else:
            string, _, right = right.partition("\"")
        key = "`@{}@`".format(str(index))
        index += 1
        assignments_dict[key] = ("\"{}\"".format(string),)
        line = "".join((left, key, right))
    return line, assignments_dict, index


def bracket_parsing(line, assignments_dict, stage, index):
    while "(" in line or "{" in line:
        i_open = 0
        bracket_close = ""
        for i, char in enumerate(line):
            if char == "(":
                bracket_close = ")"
                i_open = i
            elif char == "{":
                bracket_close = "}"
                i_open = i
            elif char == bracket_close:
                i_close = i
                key = "`@{}@`".format(str(index))
                index += 1
                if bracket_close == ")":
                    arguments, assignments_dict, index = argument_parsing(line[i_open + 1: i_close], assignments_dict,
                                                                          stage, index)
                else:
                    arguments, assignments_dict, index = alternatives_parsing(line[i_open + 1: i_close],
                                                                              assignments_dict, stage, index)
                assignments_dict[key] = arguments
                line = line[:i_open] + key + line[i_close + 1:]
                break
        else:
            raise SirilError("Unmatched brackets")
    return line, assignments_dict, index


def argument_parsing(line, assignments_dict, stage, index):
    # if "{" in line or "(" in line:
    #     raise Exception("Found bracket. Please call via bracket_parsing.")
    while "=" in line:
        # Get right most "=", split var name from previous "," or "=" or start of string
        t_line, _, arguments = line.rpartition("=")
        i_eq = t_line.rfind("=")
        i_comma = t_line.rfind(",")
        if i_comma > i_eq:
            t_line, sep, var = t_line.rpartition(",")
        elif i_eq > i_comma:
            t_line, sep, var = t_line.rpartition("=")
        else:
            # Equal, so both -1 as failed
            t_line, sep, var = "", "", t_line
        key = "`@{}@`".format(str(index))
        index += 1
        var = var.strip()
        arguments, assignments_dict, index = argument_parsing(arguments.strip(), assignments_dict, stage, index)
        # Assign it to a callable that is called by process to alter assignments_dict
        assignments_dict[key] = dynamic_assignment(var, arguments, assignments_dict)
        line = "".join((t_line, sep, key))
    arguments = [arg.strip() for arg in line.split(",") if arg]
    out = []
    for arg in arguments:
        if arg[0] in ["&", "+"]:
            out.append(PlaceNotationPerm(arg, stage))
        elif arg[0].isdigit():
            # Multiplier
            for j, char in enumerate(arg):
                if not char.isdigit():
                    break
            n = int(arg[:j])
            arg = re.sub(r"\s*\*\s*", "", arg[j:])
            for _ in range(n):
                out.append(arg)
        elif re.fullmatch(r"repeat\s*`@[0-9]+@`", arg):
            # Matches repeat and key to a bracketed expression
            key = "`@{}@`".format(str(index))
            index += 1
            assignments_dict[key] = repeat_parser(arg[6:], assignments_dict, stage, index)
            out.append(key)
        elif arg == "break":
            out.append("`@break@`")
        elif arg[0] == "@":
            # key = "`@{}@`".format(str(index))
            # index += 1
            # key2 = "`@{}@`".format(str(index))
            # index += 1
            # assignments_dict[key] = get_match(arg[1:])
            # out.append(key)
            if len(arguments) > 1:
                raise SirilError("Can't assign test with other statements")
            else:
                out = get_match(arg[1:])
        else:
            out.append(arg)
    return out, assignments_dict, index


def dynamic_assignment(var, arguments, assignments_dict):
    def assign(comp):
        # print("Dynamic assign", var, ":", arguments)
        if callable(arguments):
            assignments_dict[var] = arguments(comp)
        else:
            assignments_dict[var] = arguments
        return (), comp

    return assign


def get_match(slice_strings):
    def current_match(comp):
        return comp.current_row.match_string(slice_strings)
    return current_match


def alternatives_parsing(line, assignments_dict, stage, index):
    # if "{" in line or "(" in line:
    #     raise Exception("Found bracket. Please call via bracket_parsing.")
    statements = line.split(";")
    test_list = []
    for statement in statements:
        statement = statement.strip()
        if not statement:
            continue
        elif ":" in statement:
            test, colon, arguments = statement.partition(":")
            test = test.strip()
            # if not re.fullmatch(r"/[^/]+/", test):
            #     raise SirilError("Test must be of the form /.../", test)
        else:
            test, arguments = "", statement
        arguments, assignments_dict, index = argument_parsing(arguments, assignments_dict, stage, index)
        test_list.append((test, arguments))

    def check(comp):
        # print("Checking", test_list)
        row = comp.current_row
        for test, arguments in test_list:
            if test in assignments_dict:
                test = assignments_dict[test]
                #print(test)
            if not test or row.matches(test):
                return arguments, comp
        return [], comp

    return check, assignments_dict, index


def repeat_parser(line, assignments_dict, stage, index):
    arguments, assignments_dict, index = argument_parsing(line, assignments_dict, stage, index)

    def repeat(comp):
        try:
            assignments_dict["`@repeat@`"] = arguments
            while True:
                comp = SirilProver.process(comp, "`@repeat@`", assignments_dict)
        except StopRepeat:
            return [], comp

    return repeat


def main(text, case_sensitive=True, assignments_dict=None, statements=None):
    print(text)
    if assignments_dict is None:
        assignments_dict = {"start": (), "finish": (), "rounds": (), "everyrow": (), "abort": (),
                            "conflict": ("\"# rows ending in @\nTouch not completed due to false row$$\"",),
                            "true": ("\"# rows ending in @\nTouch is true\"",),
                            "notround": ("\"# rows ending in @\nIs this OK?\"",),
                            "false": ("\"# rows ending in @\nTouch is false in $ rows\"",),
                            "@": ("[:]",)}
    if statements is None:
        statements = {"extents": None, "bells": None, "rounds": None, "prove": None}
    if not case_sensitive:
        text = text.lower()
    # Ignore comments
    text = re.sub(r"//[^\n]*", "", text)
    # Catch trailing commas for line continuation
    text = re.sub(r",\s*\n", ", ", text)
    # Split on new lines and ; that are not within { }
    lines = re.findall(r"[^\n;]+\{.+}[^\n;]*|[^\n;{]+", text)
    index = 1
    for line in lines:
        line = line.strip()
        if line:
            if "=" in line:
                # Assignment
                if statements["bells"] is None:
                    raise SirilError("Number of bells must be defined before assignment")
                var, _, arguments = line.partition("=")
                var = var.strip()
                if var[0].isdigit():
                    raise SirilError("Definitions cannot start with a number")
                if statements["prove"] is None:
                    statements["prove"] = var
                arguments, assignments_dict, index = full_parse(arguments, assignments_dict, statements["bells"],
                                                                index)
                assignments_dict[var] = arguments
            else:
                # Statement
                match = re.match(r"([0-9]+)\s+(extents|bells)", line.lower())
                if match:
                    if statements[match.group(2)] is not None:
                        raise SirilError("Trying to reassign", match.group(2))
                    statements[match.group(2)] = int(match.group(1))
                elif line.startswith("rounds "):
                    statements["rounds"] = Row(line[7:].strip())
                elif line.startswith("prove "):
                    # To cope with assignment in the prove statement
                    statements["prove"] = "`@prove@`"
                    assignments_dict["`@prove@`"], assignments_dict, index = full_parse(line[6:].strip(),
                                                                                        assignments_dict,
                                                                                        statements["bells"], index)
                    # prove(assignments_dict, statements)
    return assignments_dict, statements


