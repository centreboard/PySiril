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
            else:
                comp = process(comp, "notround", assignments_dict)
        else:
            comp = process(comp, "false", assignments_dict)
    except StopProof as e:
        comp = e.comp
    return comp


def process(comp, var, assignments_dict):
    if callable(assignments_dict[var]):
        arguments, comp = assignments_dict[var](comp)
        if arguments:
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
                print_string(comp, arg, assignments_dict, var)
            else:
                raise SirilError("Unknown assignment", arg)
    return comp


def print_string(comp, arg, assignments_dict, var):
    # Print string
    if arg.endswith("\\\""):
        end = ""
        output = arg[1:-2]
    elif arg.endswith("\""):
        end = "\n"
        output = arg[1:-1]
    else:
        raise SirilError("Unmatched \"", arg)
    for single_use in re.findall(r"(@(\[[0-9\-]*:[0-9\-]*:?[0-9\-]*\])+)", output):
        output = output.replace(single_use[0], comp.current_row.format(single_use[0]))
    output = output.replace("@", comp.current_row.format(assignments_dict["@"][0]))
    output = output.replace("#", str(len(comp))).replace("\\n", "\n")
    if "$$" in output:
        print(output.replace("$$", "").replace("$", str(comp.number_repeated_rows())))
        if var != "abort":
            # Prevent recursion
            comp = process(comp, "abort", assignments_dict)
        raise StopProof(comp)
    if "$" in output:
        output = output.replace("$", str(comp.number_repeated_rows()))
    print(output, end=end)