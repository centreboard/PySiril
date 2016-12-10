import re
from CompositionClasses import PlaceNotationPerm, Row, Composition
from Exceptions import SirilError, StopRepeat, StopProof
import logging


logger = logging.getLogger(__name__)


def prove(assignments_dict, statements):
    logger.info("New proof")
    logger.info(assignments_dict)
    logger.info(statements)
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
                # Use a copy for post proof
                post_comp = Composition(comp.current_row, comp.stage, comp.extents)
                post_comp = process(post_comp, "post_proof", assignments_dict)
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
        arguments, comp, assignments_dict = assignments_dict[var](comp, assignments_dict)
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
                    comp.apply_perm(perm)
                    comp = process(comp, "everyrow", assignments_dict)
                    if not comp.is_true():
                        comp = process(comp, "conflict", assignments_dict)
                    if comp.current_row == assignments_dict["`@rounds@`"]:
                        comp = process(comp, "rounds", assignments_dict)
            elif arg.startswith("\""):
                print_string(comp, arg, assignments_dict, var)
            else:
                raise SirilError("Unknown assignment: {}".format(arg))
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
        raise SirilError("String not closed: {}".format(arg))
    for single_use in re.findall(r"(@(\[[0-9\-]*:[0-9\-]*:?[0-9\-]*\])+)", output):
        output = output.replace(single_use[0], comp.current_row.format(single_use[0]))
    output = output.replace("@", comp.current_row.format(assignments_dict["@"][0]))
    output = output.replace("#", str(len(comp))).replace("\\n", "\n")
    if "$$" in output:
        logger.info("$$ called by {}".format(var))
        output = output.replace("$$", "").replace("$", str(comp.number_repeated_rows()))
        if "`@output@`" in assignments_dict:
            print(output, end=end, file=assignments_dict["`@output@`"])
        else:
            print(output, end=end)
        if var != "abort":
            # Prevent recursion
            comp = process(comp, "abort", assignments_dict)
        raise StopProof(comp)
    if "$" in output:
        output = output.replace("$", str(comp.number_repeated_rows()))
    if "`@output@`" in assignments_dict:
        print(output, end=end, file=assignments_dict["`@output@`"])
    else:
        print(output, end=end)