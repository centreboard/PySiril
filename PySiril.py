#!/usr/bin/env python3
import sys
import argparse
from SirilParser import parse, default_assignments_dict, default_statements
from SirilProver import prove
from Exceptions import SirilError
from DummyFile import DummyFile

__version__ = "0.1.1"


def try_parse(siril, case_sensitive, assignments_dict, statements, line_n, assign_prove, raise_error=False):
    assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
    try:
        assignments_dict, statements = parse(siril, case_sensitive, assignments_dict, statements,
                                                    assign_prove)
    except SirilError as e:
        print("Line:", line_n, "SirilError:", e, file=assignments_dict["`@output@`"])
        if raise_error:
            raise e
        assignments_dict, statements = assignments_dict_cache, statements_cache
        success = False
    else:
        success = True
    return assignments_dict, statements, success


def try_prove(assignments_dict, statements, line_n, raise_error=False):
    # Prove does not alter the assignments or statements dictionary instances that are input
    try:
        comp, truth = prove(assignments_dict, statements)
    except SirilError as e:
        print("Line:", line_n, "SirilError:", e, file=assignments_dict["`@output@`"])
        if raise_error:
            raise e
        truth = None
    else:
        statements["prove"] = None
    return statements, truth


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--callingPositions", action="store_true",
                        help="Flag whether to import the default calling positions automatically")
    parser.add_argument("-I", "--case", action="store_false", help="Run case insensitively")
    parser.add_argument("-B", "--bells", nargs='?', type=int, help="The number of bells.")
    parser.add_argument("-n", "--extents", nargs='?', type=int, help="The number of extents. Default=1", default=1)
    parser.add_argument("-r", "--rounds", nargs='?', type=str, help="The starting 'rounds'")
    parser.add_argument("-P", "--prove", nargs='?', type=str, help="Proves given symbol", const="`@default@`")
    parser.add_argument("-M", "--method", nargs='?', type=str, help="Generates siril for a given method")
    parser.add_argument("-b", "--bob", nargs='?', type=str, const="+4", help="Place notation for bob for method")
    parser.add_argument("-s", "--single", nargs='?', type=str, const="+234", help="Place notation for bob for method")
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args()
    print("PySiril v{}".format(__version__))

    assignments_dict = default_assignments_dict
    statements = default_statements

    import_calling_position = args.callingPositions
    raise_error = args.infile != sys.stdin
    assignments_dict["`@output@`"] = args.outfile
    statements["bells"] = args.bells
    statements["extents"] = args.extents
    if args.rounds is not None:
        line = " ".join(("rounds", args.rounds))
        assignments_dict, statements, success = try_parse(line, args.case, assignments_dict, statements, 0, False,
                                                          raise_error)
    if not statements["bells"] and (args.bob or args.single or args.method):
        parser.error(
            "Please set number of bells with -B=BELLS (or implicitly with -r=ROUNDS) before using -b, -s or -M")
    if args.bob is not None:
        line = " ".join(("bob =", args.bob))
        assignments_dict, statements, success = try_parse(line, args.case, assignments_dict, statements, 0,False,
                                                          raise_error)
    if args.single is not None:
        line = " ".join(("single =", args.single))
        assignments_dict, statements, success = try_parse(line, args.case, assignments_dict, statements, 0, False,
                                                          raise_error)
    if args.method is not None:
        line = " ".join(("method", args.method))
        assignments_dict, statements, success = try_parse(line, args.case, assignments_dict, statements, 0, False,
                                                          raise_error)
    if statements["bells"]:
        if import_calling_position:
            line = "Calling Positions"
            assignments_dict, statements, success = try_parse(line, args.case, assignments_dict, statements, 0, False,
                                                              raise_error)
            if success:
                import_calling_position = False
        if args.prove is not None:
            line = " ".join(("prove", args.prove))
            t_assignment, t_statement = assignments_dict.copy(), statements.copy()
            file = DummyFile()
            t_assignment["`@output@`"] = file
            t_assignment, t_statement, success_parse = try_parse(line, args.case, t_assignment, t_statement, 0, True,
                                                                    raise_error=False)
            if success_parse:
                t_statement, success = try_prove(t_assignment, t_statement, 0, raise_error=False)
                if success:
                    file.dump(assignments_dict["`@output@`"])
                    # Prevent output at the end
                    args.prove = "`@printed@`"
    # Initialise variable which may be assigned by loop
    stored_line = ""
    truth, file = 0, DummyFile()
    for n, line in enumerate(args.infile, start=1):
        if stored_line:
            line = stored_line + line
        if line.strip("\n").strip().endswith(","):
            stored_line = line.strip("\n").strip()
            continue
        else:
            stored_line = ""

        assignments_dict, statements, success = try_parse(line, args.case, assignments_dict, statements,
                                                                 n, True, raise_error)
        if statements["bells"]:
            if import_calling_position:
                line = "Calling Positions"
                assignments_dict, statements, success = try_parse(line, args.case, assignments_dict, statements, n,
                                                                  False, raise_error)
                if success:
                    import_calling_position = False
            if args.prove is not None:
                line = " ".join(("prove", args.prove))
                t_assignment, t_statement = assignments_dict.copy(), statements.copy()
                file = DummyFile()
                t_assignment["`@output@`"] = file
                if args.prove == "`@default@`":
                    if statements["prove"] is not None:
                        print("Proving:", statements["prove"], file=file)
                        try_prove(t_assignment, t_statement, n, raise_error=False)
                elif args.prove == "`@printed@`":
                    pass
                else:
                    print("Proving:", args.prove, file=file)
                    t_assignment, t_statement, success = try_parse(line, args.case, t_assignment, t_statement,
                                                                      n, True, raise_error=False)
                    if success:
                        try_prove(t_assignment, t_statement, n, raise_error=False)
            if statements["prove"] == "`@prove@`" and (args.infile == sys.stdin or args.prove is None):
                statements, success = try_prove(assignments_dict, statements, n, raise_error)
    # Actually print last attempt at proving args.prove
    file.dump(assignments_dict["`@output@`"])


if __name__ == '__main__':
    main()
