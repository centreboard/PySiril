from math import factorial
import re

STAGE_DICT_STR_TO_INT = {"0": 10, "E": 11, "T": 12, "A": 13, "B": 14, "C": 15, "D": 16}
for bell in range(1,10):
    STAGE_DICT_STR_TO_INT[str(bell)] = bell
STAGE_DICT_INT_TO_STR = {v: k for k, v in STAGE_DICT_STR_TO_INT.items()}


class Composition:
    def __init__(self, start, stage, extents):
        self.rows = []
        self.start = start
        self.stage = stage
        self.extents = extents

    @ property
    def current_row(self):
        if self.rows:
            return self.rows[-1]
        else:
            return self.start

    def append(self, row):
        self.rows.append(row)

    def extend(self, rows):
        self.rows.extend(rows)

    def apply_place_notation(self, perm):
        self.append(self.current_row(perm))

    def is_true(self, final=False):
        # Simple common case
        if self.extents == 1:
            return len(self.rows) == len(set(self.rows))
        else:
            test_sets = [set() for _ in range(self.extents)]
            for row in self.rows:
                for t_set in test_sets:
                    if row not in t_set:
                        t_set.add(row)
                        break
                else:
                    # row is already used too many times
                    return False
            if final:
                # Checks if row used n or n-1 times
                for i in range(self.extents - 1):
                    if len(test_sets[i]) < factorial(self.stage):
                        return False
            return True

    def number_repeated_rows(self):
        # first = set()
        # repeated = set()
        # for row in self.rows:
        #     if row in first:
        #         repeated.add(row)
        #     else:
        #         first.add(row)
        # return len(repeated)
        test_sets = [set() for _ in range(self.extents + 1)]
        for row in self.rows:
            for t_set in test_sets:
                if row not in t_set:
                    t_set.add(row)
                    break
        return len(test_sets[-1])


    def __len__(self):
        return len(self.rows)


class Matcher:
    def __init__(self):
        self.cache = {}

    def match(self, test_string, row_string, stage):
        if test_string in self.cache:
            tests = self.cache[test_string]
        else:
            tests = [test_string]
            while any("[" in t for t in tests):
                new_tests = []
                for t in tests:
                    if "[" in t:
                        bells = re.search(r"\[([^\]]*)\]", t).group(1)
                        # print(bells)
                        for bell in bells:
                            new_tests.append(re.sub(r"\[[^\]]*\]", bell, t))
                            # print(new_tests)
                tests = new_tests

            # tests = [test_string]
            n = test_string.count("*")
            for i in range(n):
                new_tests = []
                for t in tests:
                    for j in range(stage - len(t.replace("*", "")) + 1):
                        new_tests.append(t.replace("*", "?" * j, 1))
                tests = new_tests
            tests = [t for t in tests if len(t) == stage]
            self.cache[test_string] = tests
        for t in tests:
            for i, bell in enumerate(t):
                if bell != "?" and bell != row_string[i]:
                    break
            else:
                return True
        else:
            return False


class Row(tuple):
    matcher = Matcher()

    def __init__(self, seq):
        self.stage = len(self)
        if len(set(self)) != self.stage:
            raise Exception("Repeated element", self)
        super().__init__()

    def __call__(self, permutation):
        return Row((self[i] for i in permutation))

    def __str__(self):
        return "".join(i if isinstance(i, str) else STAGE_DICT_INT_TO_STR[i] for i in self)

    def matches(self, test_string):
        return self.matcher.match(test_string, str(self), self.stage)


class Permutation(tuple):
    def __new__(cls, place_notation, stage):
        sequence = list(range(stage))
        i = 1 if place_notation[0] % 2 else 2
        while i < stage:
            if i in place_notation:
                i += 1
                continue
            else:
                # If not in place, must swap, index is 1 less than place
                sequence[i - 1], sequence[i] = sequence[i], sequence[i - 1]
                i += 2
        return super().__new__(cls, sequence)

    def __init__(self, place_notation, stage):
        self.stage = stage
        super().__init__()


class PlaceNotationPerm(tuple):
    def __init__(self, place_notation, stage):
        super().__init__()

    def __new__(cls, place_notation, stage):
        place_notation = place_notation.strip()
        if place_notation[0] == "&":
            symmetric = True
        elif place_notation[0] == "+":
            symmetric = False
        else:
            raise Exception("Place notation must start with & or +")
        temp = place_notation[1:].replace("x", "-").replace("-", ".-.").replace("..",".").strip(".").split(".")
        # using -1 for cross as it needs to be odd and not a valid bell
        place_notation_list = [[-1 if i == "-" else STAGE_DICT_STR_TO_INT[i] for i in place] for place in temp]
        if symmetric:
            place_notation_list += place_notation_list[-2::-1]
        return super().__new__(cls, (Permutation(place, stage) for place in place_notation_list))

if __name__ == '__main__':
    p_n = "&-3-4-2-3-4-5"
    test_row = Row(range(1, 7))
    print(test_row)
    for perm in PlaceNotationPerm(p_n, 6):
        test_row = test_row(perm)
        print(test_row, perm, test_row.matches("*5?6*"))