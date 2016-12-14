import traceback
import re
import logging
from CompositionClasses import PlaceNotationPerm, Row, Composition
from Exceptions import SirilError, StopRepeat, StopProof

logger = logging.getLogger(__name__)


def prove(in_assignments_dict, in_statements):
    # Copy to prevent proof affecting assignments elsewhere
    assignments_dict, statements = in_assignments_dict.copy(), in_statements.copy()
    logger.info("New proof")
    logger.info(assignments_dict)
    logger.info(statements)
    try:
        stage = int(statements["bells"])
    except (ValueError, TypeError):
        logger.debug("statements[\"bells\"] = {}".format(str(statements["bells"])))
        raise SirilError("Number of bells undefined")
    rounds = statements["rounds"]
    if rounds is None:
        rounds = Row(range(1, stage + 1))
    assignments_dict["`@rounds@`"] = rounds
    extents = int(statements["extents"]) if statements["extents"] else 1
    comp = Composition(rounds, stage, extents)
    try:
        comp, assignments_dict = process(comp, "start", assignments_dict)
        var = statements["prove"]
        comp, assignments_dict = process(comp, var, assignments_dict)
        comp, assignments_dict = process(comp, "finish", assignments_dict)
        final_truth = comp.is_true(True)
        if final_truth and comp.current_row == rounds:
            # Use a copy for post proof
            post_comp = Composition(comp.current_row, comp.stage, comp.extents)
            post_comp, assignments_dict = process(post_comp, "post_proof", assignments_dict)
            comp, assignments_dict = process(comp, "true", assignments_dict)
            logger.info("{} rows ending in {}. Composition is true.".format(str(len(comp)), str(comp.current_row)))
            truth = 3
        elif final_truth is None and comp.current_row == rounds:
            comp, assignments_dict = process(comp, "notextent", assignments_dict)
            logger.info("{} rows ending in {}. Not all rows appear at least {} times.".format(str(len(comp)),
                                                                                              str(comp.current_row),
                                                                                              str(extents)))
            truth = 2
        elif final_truth != 0:
            # Note this is not the same as not final_truth as catching case where final_truth is None but not at rounds
            comp, assignments_dict = process(comp, "notround", assignments_dict)
            truth = 1
            logger.info("{} rows ending in {}. Doesn't end in 'rounds'.".format(str(len(comp)),
                                                                                str(comp.current_row)))
        else:
            comp, assignments_dict = process(comp, "false", assignments_dict)
            logger.info("{} rows ending in {}. False in {} rows.".format(str(len(comp)), str(comp.current_row),
                                                                         str(comp.number_repeated_rows())))
            truth = 0
    except StopProof as e:
        comp = e.comp
        truth = None
    except RuntimeError as e:
        logger.error(traceback.format_exc())
        raise SirilError("RuntimeError: {}".format(e))
    return comp, truth


def process(comp, var, assignments_dict):
    from SirilParser import key_manager
    if callable(assignments_dict[var]):
        arguments, comp, assignments_dict = assignments_dict[var](comp, assignments_dict)
        if arguments:
            assignments_dict["`@temp@`"] = arguments
            comp, assignments_dict = process(comp, "`@temp@`", assignments_dict)
    else:
        for arg in assignments_dict[var]:
            if arg == "`@break@`":
                raise StopRepeat
            elif arg in assignments_dict:
                comp, assignments_dict = process(comp, arg, assignments_dict)
            elif isinstance(arg, PlaceNotationPerm):
                for perm in arg:
                    comp.apply_perm(perm)
                    comp, assignments_dict = process(comp, "everyrow", assignments_dict)
                    if not comp.is_true():
                        comp, assignments_dict = process(comp, "conflict", assignments_dict)
                    if comp.current_row == assignments_dict["`@rounds@`"]:
                        comp, assignments_dict = process(comp, "rounds", assignments_dict)
            elif arg.startswith("\""):
                print_string(comp, arg, assignments_dict, var)
            else:
                logger.debug("arg = {}".format(str(arg)))
                raise SirilError("Unknown assignment: {}".format(key_manager.get_original(arg)))
    return comp, assignments_dict


def print_string(comp, arg, assignments_dict, var):
    """Prints given argument string to assignments_dict["`@output@`"] or sys.stdout after formatting special char"""
    from SirilParser import key_manager
    if arg.endswith("\\\""):
        end = ""
        output = arg[1:-2]
    elif arg.endswith("\""):
        end = "\n"
        output = arg[1:-1]
    else:
        raise SirilError("String not closed: {}".format(key_manager.get_original(arg)))
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
            comp, assignments_dict = process(comp, "abort", assignments_dict)
        raise StopProof(comp)
    if "$" in output:
        output = output.replace("$", str(comp.number_repeated_rows()))
    if "`@output@`" in assignments_dict:
        print(output, end=end, file=assignments_dict["`@output@`"])
    else:
        print(output, end=end)
