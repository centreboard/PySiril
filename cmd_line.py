from SirilParser import parse
from SirilProver import prove
from Exceptions import SirilError


def main():
    assignments_dict = None
    statements = None
    assignments_dict_cache, statements_cache = None, None
    index = 1
    while 1:
        if assignments_dict is not None:
            assignments_dict_cache, statements_cache = assignments_dict.copy(), statements.copy()
        line = input(">")
        try:
            assignments_dict, statements, index = parse(line, 1, assignments_dict, statements, index)
        except SirilError as e:
            print("SirilError:", e)
            assignments_dict, statements = assignments_dict_cache, statements_cache
        #print(assignments_dict, statements)
        if statements is not None and statements["prove"] == "`@prove@`":
            prove(assignments_dict, statements)
            assignments_dict, statements = assignments_dict_cache, statements_cache
            statements["prove"] = None

if __name__ == '__main__':
    main()