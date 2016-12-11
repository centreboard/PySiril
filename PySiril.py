import sys
import argparse
from SirilParser import parse, default_assignments_dict, default_statements
from SirilProver import prove
from Exceptions import SirilError


def try_parse(siril, case_sensitive, assignments_dict, statements, index):
    assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
    try:
        assignments_dict, statements, index = parse(siril, case_sensitive, assignments_dict, statements, index)
    except SirilError as e:
        print("SirilError:", e)
        assignments_dict, statements = assignments_dict_cache, statements_cache
        success = False
    else:
        success = True
    return assignments_dict, statements, index, success


def try_prove(assignments_dict, statements):
    assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
    try:
        prove(assignments_dict, statements)
    except SirilError as e:
        print("SirilError:", e)
        assignments_dict, statements = assignments_dict_cache, statements_cache
    else:
        assignments_dict, statements = assignments_dict_cache, statements_cache
        statements["prove"] = None
    return assignments_dict, statements


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--callingPositions", action="store_true",
                        help="Flag whether to import the default calling positions automatically")
    parser.add_argument("-I", "--case", action="store_false", help="Run case insensitively")
    parser.add_argument("-B", "--bells", nargs='?', type=int, help="The number of bells.")
    parser.add_argument("-n", "--extents", nargs='?', type=int, help="The number of extents. Default 1", default=1)
    parser.add_argument("-P", "--prove", nargs='?', type=str, help="Proves given symbol")
    parser.add_argument("-M", "--method", nargs='?', type=str, help="Generates siril for a given method")
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args()

    index = 1
    assignments_dict = default_assignments_dict
    statements = default_statements

    import_calling_position = args.callingPositions
    assignments_dict["`@output@`"] = args.outfile
    statements["bells"] = args.bells
    statements["extents"] = args.extents
    if args.prove is not None:
        line = " ".join(("prove", args.prove))
        assignments_dict, statements, index, _ = try_parse(line, args.case, assignments_dict, statements, index)
    if args.method is not None:
        line = " ".join(("method", args.method))
        assignments_dict, statements, index, _ = try_parse(line, args.case, assignments_dict, statements, index)
    if import_calling_position and statements["bells"]:
        line = "Default Calling Positions"
        assignments_dict, statements, index, success = try_parse(line, args.case, assignments_dict, statements, index)
        if success:
            import_calling_position = False
    if statements["bells"] and statements["prove"] == "`@prove@`":
        assignments_dict, statements = try_prove(assignments_dict, statements)

    stored_line = ""
    for line in args.infile:
        if stored_line:
            line = stored_line + line
        if line.strip("\n").strip().endswith(","):
            stored_line = line.strip("\n").strip()
            continue
        else:
            stored_line = ""

        assignments_dict, statements, index, _ = try_parse(line, args.case, assignments_dict, statements, index)
        if import_calling_position and statements["bells"]:
            line = "Default Calling Positions"
            assignments_dict, statements, index, success = try_parse(line, args.case, assignments_dict, statements,
                                                                     index)
            if success:
                import_calling_position = False
        if statements["bells"] and statements["prove"] == "`@prove@`":
            assignments_dict, statements = try_prove(assignments_dict, statements)


if __name__ == '__main__':
    main()
