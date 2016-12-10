import sys
import argparse
from SirilParser import parse, default_assignments_dict, default_statements
from SirilProver import prove
from Exceptions import SirilError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--callingPositions", action="store_true",
                        help="Flag whether to import the default calling positions automatically")
    parser.add_argument("-I", "--case", action="store_false", help="Run case insensitively")
    parser.add_argument("-B", "--bells", nargs='?', type=int, help="The number of bells.")
    parser.add_argument("-n", "--extents", nargs='?', type=int, help="The number of extents. Default 1", default=1)
    parser.add_argument("-P", "--prove", nargs=1, type=str, help="Proves given symbol")
    parser.add_argument("-M", "--method", nargs=1, type=str, help="Generates siril for a given method")
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args()
    import_calling_position = args.callingPositions
    assignments_dict = default_assignments_dict
    statements = default_statements
    assignments_dict["`@output@`"] = args.outfile
    statements["bells"] = args.bells
    statements["extents"] = args.extents
    index = 1
    assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
    if args.prove is not None:
        line = "prove " + " ".join(args.prove)
        try:
            assignments_dict, statements, index = parse(line, args.case, assignments_dict, statements, index)
        except SirilError as e:
            print("SirilError:", e)
            assignments_dict, statements = assignments_dict_cache, statements_cache
        else:
            assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
    if args.method is not None:
        line = "method " + " ".join(args.method)
        try:
            assignments_dict, statements, index = parse(line, args.case, assignments_dict, statements, index)
        except SirilError as e:
            print("SirilError:", e)
            assignments_dict, statements = assignments_dict_cache, statements_cache
        else:
            assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
    if import_calling_position and statements["bells"]:
        try:
            assignments_dict, statements, index = parse("Default Calling Positions", args.case, assignments_dict,
                                                        statements, index)
            import_calling_position = False
        except SirilError as e:
            print("SirilError:", e)
            assignments_dict, statements = assignments_dict_cache, statements_cache
        else:
            assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
    if statements["bells"] and statements["prove"] == "`@prove@`":
        try:
            prove(assignments_dict, statements)
            assignments_dict, statements = assignments_dict_cache, statements_cache
            statements["prove"] = None
        except SirilError as e:
            print("SirilError:", e)
            assignments_dict, statements = assignments_dict_cache, statements_cache
        else:
            assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
    stored_line = ""
    for line in args.infile:
        if stored_line:
            line = stored_line + line
        if line.strip("\n").strip().endswith(","):
            stored_line = line.strip("\n").strip()
            continue
        else:
            stored_line = ""
        # line = input(">")
        try:
            assignments_dict, statements, index = parse(line, args.case, assignments_dict, statements, index)
        except SirilError as e:
            print("SirilError:", e)
            assignments_dict, statements = assignments_dict_cache, statements_cache
        else:
            assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
        if import_calling_position and statements["bells"]:
            try:
                assignments_dict, statements, index = parse("Default Calling Positions", args.case, assignments_dict,
                                                            statements, index)
                import_calling_position = False
            except SirilError as e:
                print("SirilError:", e)
                assignments_dict, statements = assignments_dict_cache, statements_cache
            else:
                assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
        if statements["bells"] and statements["prove"] == "`@prove@`":
            try:
                prove(assignments_dict, statements)
                assignments_dict, statements = assignments_dict_cache, statements_cache
                statements["prove"] = None
            except SirilError as e:
                print("SirilError:", e)
                assignments_dict, statements = assignments_dict_cache, statements_cache
            else:
                assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
                # print(assignments_dict, statements)


if __name__ == '__main__':
    main()
