import mock
from unittest import TestCase
from CompositionClasses import Composition, Row, Permutation, PlaceNotationPerm, STAGE_DICT_INT_TO_STR
from SirilProver import prove, print_string
from SirilParser import parse, default_assignments_dict
from Exceptions import StopProof, SirilError
import random
from DummyFile import DummyFile


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
                self.assertEqual(self.file.read(), "{row}{row} Aborting.\nRow={abortrow}\n".format(row=rounds,
                                                                                                   abortrow=abort_row))
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

    def check_final(self, siril, final="true", assertion=True):
        assignments_dict = self.new_assignments_dict
        comp, truth = prove(*parse(siril, assignments_dict=assignments_dict)[:2])
        # print(str(self.file))
        ending = assignments_dict[final][0].replace("#", str(len(comp))).replace("$$", "")
        ending = ending.replace("@", str(comp.current_row)).strip("\"").replace("$", str(comp.number_repeated_rows()))
        ending += "\n"
        if assertion:
            self.assertEqual(ending, self.file.read()[-len(ending):])
        else:
            self.assertNotEqual(ending, self.file.read()[-len(ending):])

    def test_plain_bob(self):
        for stage in range(6, 17, 2):
            siril = """
            {B} bells
            method Plain Bob
            Default Calling Positions
            prove 2(W, H)""".format(B=stage)
            self.check_final(siril)

    def test_stedman(self):
        for stage in range(7, 16, 2):
            plain_siril = """
            {B} bells
            method Stedman
            post_proof = +3.1, "  @"
            prove St, {x}p, +{pn}.1.3.1""".format(B=stage, x=2 * stage - 1, pn=STAGE_DICT_INT_TO_STR[stage])
            self.check_final(plain_siril)

            bob_siril = """
                        {B} bells
                        method Stedman
                        post_proof = +3.1, "- @"
                        prove St, {x}b, +{pn}.1.3.1""".format(B=stage, x=2 * (stage - 2) - 1,
                                                              pn=STAGE_DICT_INT_TO_STR[stage - 2])
            self.check_final(bob_siril)

    def test_conflict(self):
        for stage in range(4, 17):
            for extents in range(1, 10):
                siril = """
                {B} bells
                {n} extents
                x = +-
                prove {x}x""".format(B=stage, n=extents, x=2 * extents + 1)
                self.check_final(siril, "conflict")

                siril = """
                        {B} bells
                        {n} extents
                        x = +-1
                        prove {x}x""".format(B=stage, n=extents, x=2 * extents * stage)
                self.check_final(siril, "conflict")

                siril = """
                        {B} bells
                        {n} extents
                        x = +-1
                        conflict= "No dollars"
                        prove {x}x""".format(B=stage, n=extents, x=2 * extents * stage)
                self.check_final(siril, "conflict", False)
                self.check_final(siril, "true", False)
                self.check_final(siril, "false")
