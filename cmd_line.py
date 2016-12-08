from SirilParser import parse
from SirilProver import prove

def main():
    assignments_dict = None
    statements = None
    index = 1
    while 1:
        line = input(">")
        assignments_dict, statements, index = parse(line, 1, assignments_dict, statements, index)
        print(assignments_dict, statements)
        if statements["prove"] == "`@prove@`":
            prove(assignments_dict, statements)
            statements["prove"] = None

if __name__ == '__main__':
    main()