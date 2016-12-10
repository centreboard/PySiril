import mock
from unittest import TestCase
from CompositionClasses import Composition, Row, Permutation, PlaceNotationPerm, STAGE_DICT_INT_TO_STR
from SirilProver import prove, print_string
from SirilParser import parse, default_assignments_dict
from Exceptions import StopProof, SirilError
import random


class DummyFile:
    def __init__(self):
        self.buffer = []

    def write(self, string):
        self.buffer.append(string)

    def __str__(self):
        return "".join(self.buffer)

    def read(self):
        out = "".join(self.buffer)
        self.buffer = []
        return out


def random_permutation(iterable, r=None):
    """Random selection from itertools.permutations(iterable, r)"""
    pool = tuple(iterable)
    r = len(pool) if r is None else r
    return tuple(random.sample(pool, r))


class TestProver(TestCase):
    def setUp(self):
        self.default_assignments_dict = default_assignments_dict
        self.file = DummyFile()
        self.default_assignments_dict["`@output@`"] = self.file

    @property
    def new_assignments_dict(self):
        return self.default_assignments_dict.copy()

    def test_print_string(self):
        for stage in range(1, 17):
            for extents in range(1, 10):
                assignments_dict = self.default_assignments_dict.copy()
                rounds = Row(range(1, stage + 1))
                assignments_dict["`@rounds@`"] = rounds
                comp = Composition(rounds, stage, extents)
                self.assertRaises(StopProof, print_string, comp, "\"$$\"", self.default_assignments_dict, "")
                self.file.read()
                # Show abort statement works and is executed
                assignments_dict["abort"] = ("\"Aborting.\"", PlaceNotationPerm("+-", stage), "\"Row=@\"",)
                x = Permutation((-1,), stage)
                abort_row = rounds(x)
                self.assertRaises(StopProof, print_string, comp, "\"@$$@ \\\"", assignments_dict, "")
                self.assertEqual(self.file.read(), "{row}{row} Aborting.\nRow={abort_row}\n".format(row=rounds,
                                                                                                    abort_row=abort_row))
                # Test for quote closure
                self.assertRaises(SirilError, print_string, comp, "\"Not closed", self.default_assignments_dict, "")
                self.file.read()
                for _ in range(20):
                    # Testing row formatting
                    comp.apply_perm(random_permutation(range(stage)))
                    print_string(comp, "\"@\"", self.default_assignments_dict, "")
                    self.assertEqual(self.file.read(), str(comp.current_row) + "\n")
                    print_string(comp, "\"@\\\"", self.default_assignments_dict, "")
                    self.assertEqual(self.file.read(), str(comp.current_row))
                    i = random.randint(1, stage)
                    j = random.randint(1, stage)
                    k = random.randint(1, stage)
                    m = random.randint(1, stage)
                    print_string(comp, "\"@[{}:{}]\\\"".format(str(i), str(j)), self.default_assignments_dict, "")
                    self.assertEqual(self.file.read(), str(comp.current_row)[i:j])
                    print_string(comp, "\"@[{}:{}][{}:{}]\\\"".format(str(i), str(j), str(k), str(m)),
                                 self.default_assignments_dict, "")
                    self.assertEqual(self.file.read(), str(comp.current_row)[i:j] + str(comp.current_row)[k:m])

                    assignments_dict["@"] = ("[{}:{}]".format(str(j), str(k)),)
                    print_string(comp, "\"@\"", assignments_dict, "")
                    self.assertEqual(self.file.read(), str(comp.current_row)[j:k] + "\n")

                    # Comp length
                    print_string(comp, "\"#\"", self.default_assignments_dict, "")
                    self.assertEqual(int(self.file.read()), len(comp))
                    # Repeated rows
                    print_string(comp, "\"$\"", self.default_assignments_dict, "")
                    n = int(self.file.read())
                    if comp._true or comp.is_true():
                        self.assertFalse(n)
                    else:
                        self.assertEqual(n, comp.number_repeated_rows())

    def test_process(self):
        pass

    def prove_true(self, siril):
        assignments_dict = self.new_assignments_dict
        assignments_dict["true"] = (assignments_dict["true"][0], "\"{}\"".format(random.random()))
        comp = prove(*parse(siril, assignments_dict=assignments_dict)[:2])
        #print(str(self.file))
        ending = assignments_dict["true"][0].replace("#", str(len(comp)))
        ending = ending.replace("@", str(comp.current_row)).strip("\"") + "\n"
        ending += assignments_dict["true"][1].strip("\"") + "\n"
        self.assertEqual(ending, self.file.read()[-len(ending):])

    def test_plain_bob(self):
        for stage in range(6, 17, 2):
            siril = """
            {B} bells
            method Plain Bob
            Default Calling Positions
            prove 2(W, H)""".format(B=stage)
            self.prove_true(siril)

    def test_stedman(self):
        for stage in range(7, 16, 2):
            plain_siril = """
            {B} bells
            method Stedman
            post_proof = +3.1, "  @"
            prove St, {x}p, +{pn}.1.3.1""".format(B=stage, x=2 * stage - 1, pn=STAGE_DICT_INT_TO_STR[stage])
            self.prove_true(plain_siril)

            bob_siril = """
                        {B} bells
                        method Stedman
                        post_proof = +3.1, "- @"
                        prove St, {x}b, +{pn}.1.3.1""".format(B=stage, x=2 * (stage - 2) - 1,
                                                              pn=STAGE_DICT_INT_TO_STR[stage - 2])
            self.prove_true(bob_siril)
