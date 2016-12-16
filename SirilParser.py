import os
import re
from textwrap import dedent
import logging
import SirilProver
from CompositionClasses import PlaceNotationPerm, Row, STAGE_DICT_INT_TO_STR, Composition
from Exceptions import SirilError, StopRepeat, ImportFileNotFound
from MethodImport import get_method, stages


logger = logging.getLogger(__name__)


class KeyManager:
    def __init__(self):
        self.index = 1
        self.original = {}
        self.re = re.compile(r"`@[0-9]+@`")

    def get_key(self, replace):
        key = "`@{}@`".format(str(self.index))
        self.index += 1
        # Ensure no keys in stored cache.
        stored = self.get_original(replace)
        self.original[key] = stored
        return key

    def get_original(self, line):
        out = line
        for key in self.re.findall(line):
            out = out.replace(key, self.original[key])
        return out


def full_parse(line, assignments_dict, stage, case_sensitive=True):
    line, assignments_dict = string_parsing(line, assignments_dict)
    if not case_sensitive:
        line = line.lower()
    line, assignments_dict = external_parsing(line, assignments_dict, stage)
    line, assignments_dict = bracket_parsing(line, assignments_dict, stage)
    out, assignments_dict = argument_parsing(line, assignments_dict, stage)
    return out, assignments_dict


def string_parsing(line, assignments_dict):
    line = line.replace("'", "\"")
    while "\"" in line:
        left, _, right = line.partition("\"")
        if "\"" not in right:
            raise SirilError("String not closed: {}".format(key_manager.get_original(line)))
        else:
            string, _, right = right.partition("\"")
        # Check further statements on line are after a comma or semicolon or bracket
        if right.strip() and right.strip()[0] not in [",", ";", ")", "}"] and right.strip()[:2] != "!)":
            raise SirilError("No comma or semicolon between statements: {}".format(key_manager.get_original(right)))
        # key = "`@{}@`".format(str(index))
        # index += 1
        key = key_manager.get_key("\"{}\"".format(string))
        assignments_dict[key] = ("\"{}\"".format(string),)
        line = "".join((left, key, right))
    return line, assignments_dict


def external_parsing(line, assignments_dict, stage):
    while "[!" in line:
        i_open = None
        bracket_close = ""
        for i, char in enumerate(line):
            # Protect from indexing errors when accessing line[i+-1] It will fall through to else.
            if char == "[" and len(line) > i and line[i+1] == "!":
                bracket_close = "]"
                i_open = i
            elif char == bracket_close and i and line[i-1] == "!":
                if i_open is None:
                    raise SirilError("!] before [!: {}".format(key_manager.get_original(line)))
                i_close = i
                arguments, assignments_dict = external_parser(line[i_open + 2: i_close - 1], assignments_dict, stage)
                # Include brackets in the original
                key = key_manager.get_key(line[i_open: i_close + 1])
                assignments_dict[key] = arguments
                line = line[:i_open] + key + line[i_close + 1:]
                break
        else:
            raise SirilError("Unmatched external parsing brackets [! !]: {}".format(key_manager.get_original(line)))
    if "!]" in line:
        raise SirilError("Unmatched external parsing brackets [! !]: {}".format(key_manager.get_original(line)))
    return line, assignments_dict


def bracket_parsing(line, assignments_dict, stage):
    # Works from inner pair towards outer pairs
    while "(" in line or "{" in line:
        i_open = None
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
                if bracket_close == ")":
                    arguments, assignments_dict = argument_parsing(line[i_open + 1: i_close], assignments_dict, stage)
                else:
                    arguments, assignments_dict = alternatives_parsing(line[i_open + 1: i_close], assignments_dict,
                                                                       stage)
                # Include brackets in the original
                key = key_manager.get_key(line[i_open: i_close + 1])
                assignments_dict[key] = arguments
                line = line[:i_open] + key + line[i_close + 1:]
                break
        else:
            raise SirilError("Unmatched brackets: {}".format(key_manager.get_original(line)))
    if ")" in line or "}" in line:
        raise SirilError("Unmatched brackets: {}".format(key_manager.get_original(line)))
    return line, assignments_dict


def argument_parsing(line, assignments_dict, stage):
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
        # key = "`@{}@`".format(str(index))
        # index += 1
        key = key_manager.get_key("{} = {}".format(var, arguments))
        var = var.strip()
        if var[0].isdigit():
            raise SirilError("Definitions cannot start with a number")
        arguments, assignments_dict = argument_parsing(arguments.strip(), assignments_dict, stage)
        # Assign it to a callable that is called by process to alter assignments_dict
        assignments_dict[key] = dynamic_assignment(var, arguments)
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
            else:
                raise SirilError("Argument is all digits: {}".format(key_manager.get_original(arg)))
            n = int(arg[:j])
            arg = re.sub(r"\s*\*\s*", "", arg[j:]).strip()
            # TODO: if arg not in assignments_dict
            for _ in range(n):
                out.append(arg)
        elif re.fullmatch(r"repeat\s*`@[0-9]+@`", arg):
            # Matches repeat and a key to a processed bracketed expression
            # key = "`@{}@`".format(str(index))
            # index += 1
            key = key_manager.get_key(arg)
            assignments_dict[key], assignments_dict = repeat_parser(arg[6:], assignments_dict, stage)
            out.append(key)
        elif arg == "break":
            out.append("`@break@`")
        elif arg[0] == "@":
            if len(arguments) > 1:
                raise SirilError("Can't assign test ({}) with other statements".format(key_manager.get_original(arg)))
            else:
                out = get_match(arg[1:])
        else:
            out.append(arg)
    return out, assignments_dict


def dynamic_assignment(var, arguments):
    def assign(comp, assignments_dict):
        logger.info("Dynamic Assignment {var}: {arg}".format(var=var, arg=arguments))
        if callable(arguments):
            assignments_dict[var] = arguments(comp)
        else:
            # if var in arguments:
            new_arguments = []
            for x in arguments:
                if x == var:
                    new_arguments.extend(assignments_dict[var])
                else:
                    new_arguments.append(x)
            assignments_dict[var] = new_arguments
        return (), comp, assignments_dict

    return assign


def get_match(slice_strings):
    def current_match(comp):
        return comp.current_row.match_string(slice_strings)

    return current_match


def alternatives_parsing(line, assignments_dict, stage):
    statements = line.split(";")
    test_list = []
    for statement in statements:
        statement = statement.strip()
        if not statement:
            continue
        elif ":" in statement:
            test, colon, arguments = statement.partition(":")
            test = test.strip()
        else:
            test, arguments = "", statement
        arguments, assignments_dict = argument_parsing(arguments, assignments_dict, stage)
        test_list.append((test, arguments))

    def check(comp, check_assignments_dict):
        row = comp.current_row
        for check_test, check_arguments in test_list:
            if check_test in check_assignments_dict:
                check_test = check_assignments_dict[check_test]
            if not check_test or row.matches(check_test):
                break
        else:
            check_arguments = ()
        return check_arguments, comp, check_assignments_dict

    return check, assignments_dict


def repeat_parser(line, assignments_dict, stage):
    arguments, assignments_dict = argument_parsing(line, assignments_dict, stage)

    def repeat(comp, inner_assignments_dict):
        try:
            inner_assignments_dict["`@repeat@`"] = arguments
            n = 0
            while True:
                n += 1
                if n > 100000:
                    raise SirilError("Recursion Error in repeat loop")
                comp, inner_assignments_dict = SirilProver.process(comp, "`@repeat@`", inner_assignments_dict)

        except StopRepeat:
            return [], comp, inner_assignments_dict

    return repeat, assignments_dict


def external_parser(line, assignments_dict, stage):
    # Don't need case sensitive. If it is it will already be lowered.
    # Full parse should fall straight through string and external as already dealt with but catches any other
    # brackets in the line
    arguments, assignments_dict = full_parse(line, assignments_dict, stage)

    def external(comp, inner_assignments_dict):
        # Use a copy for external use and return the original comp untouched
        inner_assignments_dict["`@external@`"] = arguments
        ext_comp = Composition(comp.current_row, comp.stage, comp.extents)
        ext_comp, inner_assignments_dict = SirilProver.process(ext_comp, "`@external@`", inner_assignments_dict)
        return [], comp, inner_assignments_dict

    return external, assignments_dict


def parse(text, case_sensitive=True, assignments_dict=None, statements=None, assign_prove=True):
    logger.info("New parse of lines:\n{}".format(text))
    logger.debug("""
    assignments_dict in: {}
    statements_in: {}""".format(str(assignments_dict), str(statements)))
    if assignments_dict is None:
        assignments_dict = default_assignments_dict.copy()
    if statements is None:
        statements = default_statements.copy()
    # Ignore comments
    text = re.sub(r"//[^\n]*", "", text)
    # Catch trailing commas for line continuation
    text = re.sub(r",\s*\n", ", ", text)
    # Split on new lines and ; that are not within { }
    lines = re.findall(r"[^\n;]+\{.+\}[^\n;]*|[^\n;{]+", text)
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ("=" in line and not line.startswith("prove ")) or line.startswith("prove ="):
            # Assignment
            if statements["bells"] is None:
                raise SirilError("Number of bells must be defined before assignment")
            assignments_dict, statements = variable_assignment(line, assignments_dict, case_sensitive, statements,
                                                               assign_prove)
        else:
            # Statement
            match = re.match(r"([0-9]+)\s+(extents|bells)", line.lower())
            if match:
                if match.group(2) == "bells" and statements["bells"]:
                    if int(match.group(1)) == statements[match.group(2)]:
                        logger.info("Assigning bells to same value")
                    else:
                        raise SirilError("Trying to reassign bells")
                else:
                    statements[match.group(2)] = int(match.group(1))
            elif line.lower().startswith("import "):
                file_name = "{}.siril".format(line[7:]) if "." not in line else line[7:]
                assignments_dict, statements = import_siril(file_name, case_sensitive, assignments_dict, statements)
            elif line.lower().startswith("rounds "):
                statements["rounds"] = Row(line[7:].strip())
                if statements["bells"] is not None:
                    if statements["rounds"].stage != statements["bells"]:
                        raise SirilError("Rounds not same length as number of bells")
                else:
                    statements["bells"] = statements["rounds"].stage
            elif line.lower().startswith("prove ") and assign_prove:
                # To cope with assignment in the prove statement
                statements["prove"] = "`@prove@`"
                assignments_dict["`@prove@`"], assignments_dict = full_parse(line[6:].strip(), assignments_dict,
                                                                             statements["bells"])
            elif statements["bells"] is not None and line.lower().startswith("method "):
                method_siril = import_method(line, statements)
                assignments_dict, statements = parse(method_siril, case_sensitive, assignments_dict, statements, False)
            elif statements["bells"] is not None and line.title() == "Calling Positions":
                tenor = STAGE_DICT_INT_TO_STR[statements["bells"]]
                assignments_dict, statements = parse(calling_position_siril(tenor), case_sensitive, assignments_dict,
                                                     statements, False)
            else:
                if "`@output@`" in assignments_dict:
                    print("Statement has no effect:", line, file=assignments_dict["`@output@`"])
                else:
                    print("Statement has no effect:", line)
                logger.info("Statement has no effect: {}".format(line))
    logger.debug("assignments_dict out: {}\n\tstatements out: {}".format(str(assignments_dict), str(statements)))
    return assignments_dict, statements


def import_method(line, statements):
    if "\"" in line:
        method_title, short = line.split("\"")[:2]
        method_title = method_title[7:].strip()
    else:
        method_title = line[7:].strip()
        short = method_title[:2]
    for stage, title in stages.items():
        if method_title.lower().endswith(title):
            break
    else:
        method_title += " {}".format(str(stages[statements["bells"]]))
    method_siril = get_method(method_title, short)
    return method_siril


def import_siril(file_name, case_sensitive, assignments_dict, statements):
    import_name = ""
    for dir_path, dirs, files in filter(lambda y: not y[0].startswith("./.git"), os.walk("./")):
        for name in files:
            if name == file_name:
                import_name = os.path.join(dir_path, name)
                break
        if import_name:
            break
    try:
        with open(import_name) as f:
            assignments_dict, statements = parse(f.read(), case_sensitive, assignments_dict, statements, False)
    except FileNotFoundError:
        raise ImportFileNotFound(file_name)
    return assignments_dict, statements


def variable_assignment(line, assignments_dict, case_sensitive, statements, assign_prove):
    var, _, arguments = line.partition("=")
    var = var.strip()
    if var[0].isdigit():
        raise SirilError("Definitions cannot start with a number")
    if not case_sensitive:
        var = var.lower()
    if statements["prove"] is None and assign_prove:
        statements["prove"] = var
    arguments, assignments_dict = full_parse(arguments, assignments_dict, statements["bells"], case_sensitive)
    if not callable(arguments) and var in arguments:
        new_arguments = []
        for x in arguments:
            if x == var:
                new_arguments.extend(assignments_dict[var])
            else:
                new_arguments.append(x)
        arguments = new_arguments
    assignments_dict[var] = arguments
    return assignments_dict, statements


def calling_position_siril(tenor):
    return dedent(r"""
    H = repeat(method, {{/*{tenor}?/: b, break; p}})
    sH = repeat(method, {{/*{tenor}?/: s, break; p}})
    pH = repeat(method, {{/*{tenor}?/: p, break; p}})
    W = repeat(method, {{/*{tenor}/: b, break; p}})
    sW = repeat(method, {{/*{tenor}/: s, break; p}})
    M = repeat(method, {{/*{tenor}???/: b, break; p}})
    sM = repeat(method, {{/*{tenor}???/: s, break; p}})
    B = repeat(method, {{/1{tenor}*/: b, break; p}})
    """.format(tenor=tenor))


default_assignments_dict = {"start": (), "finish": (), "rounds": (), "everyrow": (), "abort": (), "post_proof": (),
                            "conflict": ("\"# rows ending in @\nTouch not completed due to false row$$\"",),
                            "true": ("\"# rows ending in @\nTouch is true\"",),
                            "notround": ("\"# rows ending in @\nIs this OK?\"",),
                            "false": ("\"# rows ending in @\nTouch is false in $ rows\"",),
                            "notextent": (
                                "\"# rows ending in @\nNot all rows appear at least (no. extents - 1) times\"",),
                            "@": ("[:]",)}
default_statements = {"extents": None, "bells": None, "rounds": None, "prove": None}

key_manager = KeyManager()
