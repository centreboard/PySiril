import sys
import argparse
from SirilParser import parse, default_assignments_dict, default_statements
from SirilProver import prove
from Exceptions import SirilError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--callingPositions", action="store_true",
                        help="Flag whether to import the default calling positions automatically")
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args()
    import_calling_position = args.callingPositions
    assignments_dict = default_assignments_dict
    statements = default_statements
    assignments_dict["`@output@`"] = args.outfile
    index = 1
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
        #line = input(">")
        try:
            assignments_dict, statements, index = parse(line, 1, assignments_dict, statements, index)
        except SirilError as e:
            print("SirilError:", e)
            assignments_dict, statements = assignments_dict_cache, statements_cache
        else:
            assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
        if import_calling_position and statements["bells"]:
            try:
                assignments_dict, statements, index = parse("Default Calling Positions", 1, assignments_dict,
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
        #print(assignments_dict, statements)


if __name__ == '__main__':
    main()