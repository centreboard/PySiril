import re
from math import factorial
from typing import List
from Exceptions import SirilError

STAGE_DICT_STR_TO_INT = {"0": 10, "E": 11, "T": 12, "A": 13, "B": 14, "C": 15, "D": 16}
for bell in range(1, 10):
    STAGE_DICT_STR_TO_INT[str(bell)] = bell
STAGE_DICT_INT_TO_STR = {v: k for k, v in STAGE_DICT_STR_TO_INT.items()}
for key, value in tuple(STAGE_DICT_STR_TO_INT.items()):
    # Add lower case versions
    STAGE_DICT_STR_TO_INT[key.lower()] = value


class Matcher:
    def __init__(self):
        self.cache = {}

    def match(self, test_string, row_string, stage):
        if not test_string.startswith("/") or not test_string.endswith("/"):
            raise SirilError("Test must be of the form /.../", test_string)
        test_string = test_string.strip("/")
        if test_string in self.cache:
            tests = self.cache[test_string]
        else:
            tests = [test_string]
            # [12] is 1 or 2 in this place
            while any("[" in t for t in tests):
                new_tests = []
                for t in tests:
                    if "[" in t:
                        # Get a sting of bells from within brackets. Note bells are 1 char, alphanumeric.
                        bells = re.search(r"\[([^\]]*)\]", t).group(1)
                        # Iterate bell by bell
                        for bell in bells:
                            new_tests.append(re.sub(r"\[[^\]]*\]", bell, t))
                tests = new_tests

            # * is an arbitary number. Instance by instance fill the string with possible amounts then prune those
            # still too short
            # i.e. for 4 bell *2* becomes:
            # 2*, ?2*, ??2* then 2, 2?, 2??, 2???, ?2, ?2?, ?2?? etc.
            n = test_string.count("*")
            for i in range(n):
                new_tests = []
                for t in tests:
                    for j in range(stage - len(t.replace("*", "")) + 1):
                        new_tests.append(t.replace("*", "?" * j, 1))
                tests = new_tests
            tests = [t for t in tests if len(t) == stage]
            self.cache[test_string] = tests
        # And test if matches
        for t in tests:
            for i, bell in enumerate(t):
                if bell != "?" and bell != row_string[i]:
                    break
            else:
                return True
        else:
            return False


class Row(tuple):
    # Single Matcher instance for all rows
    matcher = Matcher()
    #[Start:Stop:Step] where :step is optional, as are start and stop values
    slice_re = re.compile(r"\[([0-9\-]*:[0-9\-]*:?[0-9\-]*)\]")

    def __init__(self, seq):
        self.stage = len(self)
        if len(set(self)) != self.stage:
            raise SirilError("Repeated element in row {}".format(str(self)))
        super().__init__()

    def __call__(self, permutation):
        return Row((self[i] for i in permutation))

    def __str__(self):
        return "".join(i if isinstance(i, str) else STAGE_DICT_INT_TO_STR[i] for i in self)

    def format(self, style):
        """Style is a string
        [:] = all
        [2:4] = slice
        [:2][6:] = two slices added together"""
        style = style.strip("\"")
        if style == "[:]":
            out = str(self)
        else:
            out = []
            for slice_string in self.slice_re.findall(style):
                s = self.get_slice(slice_string)
                out.append("".join(i if isinstance(i, str) else STAGE_DICT_INT_TO_STR[i] for i in self[s]))
            out = "".join(out)
        return out

    def match_string(self, slice_strings):
        indices = []
        for slice_string in self.slice_re.findall(slice_strings):
            s = self.get_slice(slice_string)
            indices.extend(range(s.start, s.stop, s.step))
        return "/" + "".join((STAGE_DICT_INT_TO_STR[self[i]] if i in indices else "?" for i in range(self.stage))) + "/"

    def get_slice(self, slice_string):
        start, colon, stop = slice_string.partition(":")
        if ":" in stop:
            stop, colon, step = stop.partition(":")
            step = int(step) if step else 1
        else:
            step = 1
        start = int(start) if start else 0
        stop = int(stop) if stop else self.stage
        return slice(start, stop, step)

    def matches(self, test_string):
        return Row.matcher.match(test_string, str(self), self.stage)


class Permutation(tuple):
    def __new__(cls, place_ints: List[int], stage: int):
        # Integrity check
        for place in place_ints:
            if place > stage:
                raise SirilError("Place notation greater than current number bells: {}".format(
                    STAGE_DICT_INT_TO_STR[place]))
        sequence = list(range(stage))
        i = 1 if place_ints[0] % 2 else 2
        while i < stage:
            if i in place_ints:
                i += 1
                continue
            else:
                # If not in place, must swap, index is 1 less than place
                sequence[i - 1], sequence[i] = sequence[i], sequence[i - 1]
                i += 2
        return super().__new__(cls, sequence)

    def __init__(self, place_ints, stage):
        self.stage = stage
        super().__init__()


class PlaceNotationPerm(tuple):
    def __init__(self, place_notation: str, stage: int):
        super().__init__()

    def __new__(cls, place_notation, stage):
        place_notation = place_notation.strip()
        if place_notation[0] == "&":
            symmetric = True
        elif place_notation[0] == "+":
            symmetric = False
        else:
            raise Exception("Place notation must start with & or +")
        temp = place_notation[1:].replace("x", "-").replace("-", ".-.").replace("..", ".").strip(".").split(".")
        # using -1 for cross as it needs to be odd and not a valid bell
        try:
            place_notation_list = [[-1 if i == "-" else STAGE_DICT_STR_TO_INT[i] for i in place] for place in temp]
        except KeyError:
            raise SirilError("Invalid place notation: {}".format(place_notation))
        if symmetric:
            place_notation_list += place_notation_list[-2::-1]
        return super().__new__(cls, (Permutation(place, stage) for place in place_notation_list))


class Composition:
    def __init__(self, start: Row, stage: int, extents: int):
        self.rows = []
        self.row_set = set()
        self.start = start
        self.stage = stage
        self.extents = extents
        self._true = True

    @property
    def current_row(self):
        if self.rows:
            return self.rows[-1]
        else:
            return self.start

    def append(self, row):
        if self._true and row in self.row_set:
            self._true = None
        self.rows.append(row)
        self.row_set.add(row)

    def extend(self, rows):
        for row in rows:
            self.append(row)

    def apply_perm(self, perm):
        self.append(self.current_row(perm))

    def is_true(self, final=False):
        if final or self._true is None:
            # Simple common case
            if self.extents == 1:
                self._true = len(self.rows) == len(set(self.rows))
            else:
                test_sets = [set() for _ in range(self.extents)]
                for row in self.rows:
                    for t_set in test_sets:
                        if row not in t_set:
                            t_set.add(row)
                            break
                    else:
                        # row is already used too many times
                        self._true = False
                        break
                else:
                    # Set row_set to last set, as most interested if row is in this one. The row cascades down when it
                    # becomes dirty.
                    self._true = True
                    self.row_set = test_sets[-1]
                    if final:
                        # Checks if row used n or n-1 times
                        for i in range(self.extents - 1):
                            if len(test_sets[i]) < factorial(self.stage):
                                self._true = None
                                break
        return self._true

    def number_repeated_rows(self):
        """Returns number of rows featuring n + 1 times (i.e. are false in a n extent composition"""
        # This is <= len(row_set) as rows are first added to row_set instead of lower down.
        test_sets = [set() for _ in range(self.extents + 1)]
        for row in self.rows:
            for t_set in test_sets:
                if row not in t_set:
                    t_set.add(row)
                    break
        return len(test_sets[-1])

    def __len__(self):
        return len(self.rows)

    def __iter__(self):
        for row in self.rows:
            yield row


if __name__ == '__main__':
    p_n = "&-3-4-2-3-4-5"
    test_row = Row(range(1, 7))
    print(test_row)
    for test_perm in PlaceNotationPerm(p_n, 6):
        test_row = test_row(test_perm)
        print(test_row, test_perm, test_row.matches("*5?6*"))
