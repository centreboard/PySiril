import re
from CompositionClasses import PlaceNotationPerm, Row, Composition
from Exceptions import SirilError, StopRepeat, StopProof


def prove(assignments_dict, statements):
    print(assignments_dict)
    print(statements)
    try:
        stage = int(statements["bells"])
    except ValueError:
        raise SirilError("Number of bells undefined")
    rounds = statements["rounds"]
    if rounds is None:
        rounds = Row(range(1, stage + 1))
    assignments_dict["`@rounds@`"] = rounds
    extents = int(statements["extents"]) if statements["extents"] else 1
    comp = Composition(rounds, stage, extents)
    try:
        comp = process(comp, "start", assignments_dict)
        var = statements["prove"]
        comp = process(comp, var, assignments_dict)
        comp = process(comp, "finish", assignments_dict)
        if comp.is_true(True):
            if comp.current_row == rounds:
                comp = process(comp, "true", assignments_dict)
                # print("True composition.\n{} rows ending in {}".format(len(comp), rounds))
            else:
                comp = process(comp, "notround", assignments_dict)
                # print("Composition doesn't end in rounds.\n", len(comp), "rows ending in", comp.current_row)
        else:
            comp = process(comp, "false", assignments_dict)
    except StopProof as e:
        comp = e.comp
    return comp


def process(comp, var, assignments_dict):
    if callable(assignments_dict[var]):
        arguments, comp = assignments_dict[var](comp)
        assignments_dict["`@temp@`"] = arguments
        comp = process(comp, "`@temp@`", assignments_dict)
    else:
        for arg in assignments_dict[var]:
            if arg == "`@break@`":
                raise StopRepeat
            elif arg in assignments_dict:
                comp = process(comp, arg, assignments_dict)
            elif isinstance(arg, PlaceNotationPerm):
                for perm in arg:
                    comp.apply_place_notation(perm)
                    comp = process(comp, "everyrow", assignments_dict)
                    if not comp.is_true():
                        comp = process(comp, "conflict", assignments_dict)
                    if comp.current_row == assignments_dict["`@rounds@`"]:
                        comp = process(comp, "rounds", assignments_dict)
            elif arg.startswith("\""):
                if arg.endswith("\\\""):
                    end = ""
                    output = arg[1:-2]
                elif arg.endswith("\""):
                    end = "\n"
                    output = arg[1:-1]
                else:
                    raise SirilError("Unmatched \"", arg)
                output = output.replace("@", str(comp.current_row)).replace("#", str(len(comp))).replace("\\n", "\n")
                if "$$" in output:
                    print(output.replace("$$", "").replace("$", str(comp.number_repeated_rows())))
                    if var != "abort":
                        # Prevent recursion
                        comp = process(comp, "abort", assignments_dict)
                    raise StopProof(comp)
                output = output.replace("$", str(comp.number_repeated_rows()))
                print(output, end=end)
    return comp


def string_parsing(line, assignments_dict, stage, index):
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
        print(line)
    return bracket_parsing(line, assignments_dict, stage, index)


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
                    arguments, assignments_dict, index = alternatives(line[i_open + 1: i_close], assignments_dict,
                                                                      stage, index)
                assignments_dict[key] = arguments
                line = line[:i_open] + key + line[i_close + 1:]
                break
        else:
            raise SirilError("Unmatched brackets")
    return argument_parsing(line, assignments_dict, stage, index)


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
            # Matches repeat and key to a bracketted expression
            key = "`@{}@`".format(str(index))
            index += 1
            assignments_dict[key] = repeat_parser(arg[6:], assignments_dict, stage, index)
            out.append(key)
        elif arg == "break":
            out.append("`@break@`")
        else:
            out.append(arg)
    return out, assignments_dict, index


def dynamic_assignment(var, arguments, assignments_dict):
    def assign(comp):
        # print("Dynamic assign", var, ":", arguments)
        assignments_dict[var] = arguments
        return [], comp

    return assign


def alternatives(line, assignments_dict, stage, index):
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
            if not re.fullmatch(r"/[^/]+/", test):
                raise SirilError("Test must be of the form /.../", test)
        else:
            test, arguments = "", statement
        arguments, assignments_dict, index = argument_parsing(arguments, assignments_dict, stage, index)
        test_list.append((test[1:-1], arguments))

    def check(comp):
        # print("Checking", test_list)
        row = comp.current_row
        for test, arguments in test_list:
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
                comp = process(comp, "`@repeat@`", assignments_dict)
        except StopRepeat:
            return [], comp

    return repeat


def main(text):
    print(text)
    assignments_dict = {"start": (), "finish": (), "rounds": (), "everyrow": (), "abort": (),
                        "conflict": ("\"# rows ending in @\nTouch not completed due to false row$$\"",),
                        "true": ("\"# rows ending in @\nTouch is true\"",),
                        "notround": ("\"# rows ending in @\nIs this OK?\"",),
                        "false": ("\"# rows ending in @\nTouch is false in $ rows\"",)}
    statements = {"extents": None, "bells": None, "rounds": None, "prove": None}
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
                arguments, assignments_dict, index = string_parsing(arguments, assignments_dict, statements["bells"],
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
                    assignments_dict["`@prove@`"], assignments_dict, index = string_parsing(line[6:].strip(),
                                                                                            assignments_dict,
                                                                                            statements["bells"], index)
                    # prove(assignments_dict, statements)
    prove(assignments_dict, statements)


if __name__ == '__main__':
    test_input_1 = r"""

        6 bells
        Cm = &-3-4-2-3-4-5
        p = Cm, +2, {/16*/: "  @"}
        b = Cm, +4, "- @"
        comp = 2(2p,b,p,b)
        prove comp
        """
    test_input_2 = r"""
        6 bells;
        b = +4;
        Cm = &-3-4-2-3-4-5, (p = +2);
        Pr = &-3-4-2-3-4-5, (p = +6);
        comp =  3(Cm,b,Cm,p,Pr,p,Pr,p,Cm,p,Cm,b,Cm,p,Pr,p,Pr,p,Cm,b);
        prove comp
        """
    test_input_3 = r"""
        6 bells;
        lh = "\";

        start  = "  @ \";
        finish = lh, "\n";

        p2lh = +2,   "  @ \";
        p6lh = +6,   "  @ \";
        blh  = +4,   "- @ \";

        lh2 = (p = lh=p2lh), (b = lh=blh), (lh=p2lh);
        lh6 = (p = lh=p6lh), (b = lh=blh), (lh=p6lh);

        Cm = lh, &-3-4-2-3-4-5, lh2, "Cm"; // Cambridge
        Pr = lh, &-3-4-2-3-4-5, lh6, "Pr"; // Primrose

        prove 3( Cm,b,Cm,Pr,Pr,Cm,Cm,b,Cm,Pr,Pr,Cm,b );
        """
    test_input_4 = r"""
    6 bells;

    m = &-3-4-2-3-4-5;

    p = +2, "  @";
    b = +4, "- @";

    W = repeat( m, {/*6/:  b, break; p} )
    H = repeat( m, {/*6?/: b, break; p} )

    finish = repeat(m, p, {/123456/: break})

    prove 3(W,H,W)
    """
    test_false_1 = r"""
    8 bells
    2 extents
    everyrow = "@"
    abort = "HI there"
    conflict=
    prove 10(&xxx,+x)"""
    test_dixons = """
    // 720 Dixon's Bob Minor.   Comp. A.E.Holroyd.

    6 bells;

    lead = repeat( +x, { /1*/: break; /[24]*/: +14; +16 } );

    p = lead, +12,   "  @";
    b = lead, +14,   "- @";
    s = lead, +1234, "s @";

    prove 4p,s,4p,b,4p,p,4p,b,
          4p,b,4p,b,4p,s,4p,b,
          4p,b,4p,b,4p,p,4p,b"""

    test_magic = r"""
    // 720 Spliced Treble Dodging Minor.   Comp. P.A.B.Saddleton.

    6 bells;

    printlh = over,under,"\n  @ \", over;
    printhl = under, " @ \";

    mid1 = +-2-; // p.n. when treble is dodging 3-4 up
    mid2 = +-2-; // p.n. when treble is dodging 3-4 down

    // Overworks
    A = +4.5-3.2,   (over="A\"), printlh, +3-5.4,  mid1;  // George Orwell
    B = +4-34-2,    (over="B\"), printlh, +-34-4,  mid1;  // Westminster
    C = +4.3-3.2,   (over="C\"), printlh, +3-3.4,  mid1;  // London
    D = +4.3-34.2,  (over="D\"), printlh, +34-3.4, mid1;  // Carlisle
    E = +4-3-2,     (over="E\"), printlh, +-3-4,   mid1;  // Cambridge

    // Underworks
    a = +3-34-5,    (under="a\"),printhl, +-34-3,  mid2;  // S2 (aka Rhyl)
    b = +3.4-4.5,   (under="b\"),printhl, +4-4.3,  mid2;  // Chelsea
    c = +3.2-4.5,   (under="c\"),printhl, +4-2.3,  mid2;  // Kelso
    d = +3.4-34.5,  (under="d\"),printhl, +34-4.3, mid2;  // Beverley
    e = +3-4-5,     (under="e\"),printhl, +-4-3,   mid2;  // Cambridge

    // Opening half-lead -- start midway through a D overwork
    firstsection = "  @ D\", +34-3.4

    // Which bells pivot for which over/underworks?
    above = { /2*/: D; /3*/: C; /4*/: E; /5*/: B; /6*/: A; };
    below = { /*2/: e; /*3/: c; /*4/: d; /*5/: b; /*6/: a; };

    // Tidy up and exit when rounds occurs
    rounds = over,under,"", break;

    prove firstsection, mid1, repeat (below, above);"""

    test_input_5 = r"""
    8 bells
    B=repeat(Sup,{/18*/:b,break;p})
    M=repeat(Sup,{/*8???/:b,break;p})
    sM=repeat(Sup,{/*8???/:s,break;p})
    sW=repeat(Sup,{/*8/:s,break;p})
    sH =repeat(Sup,{/*8?/:s,break;p})
    end=repeat({/12345678/:break;Sup,p})
    s=+234,"s @"
    b=+4,"- @"
    p=+2
    Sup=&x36x4x5x36x4x5x36x7
    snap = " (12536478)",+x4x5x36x4x5x36x7x36x5x4x36x5x4x36x2

prove snap, 2(sM, M), sW, sH, B, sW, B, end"""
    main(test_input_1)
    main(test_input_2)
    main(test_input_3)
    main(test_input_4)
    main(test_dixons)
    main(test_magic)
    main(test_input_5)
    main(test_false_1)
