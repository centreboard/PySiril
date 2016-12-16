from unittest import TestCase
from SirilParser import *
from Exceptions import SirilError
from DummyFile import DummyFile


class TestParse(TestCase):
    def setUp(self):
        self.default_assignments_dict = default_assignments_dict.copy()
        self.default_statements = default_statements.copy()
        self.file = DummyFile()
        self.default_assignments_dict["`@output@`"] = self.file

    @property
    def new_assignments_dict(self):
        return self.default_assignments_dict.copy()

    def test_parse(self):
        self.fail()

    def test_argument_parsing(self):
        self.fail()

    def test_bracket_parsing(self):
        self.fail()

    def test_string_parsing(self):
        line = "\"Test\""
        assignments_dict = self.new_assignments_dict
        out_line, assignments_dict = string_parsing(line, assignments_dict)
        self.assertNotIn(line, assignments_dict)
        self.assertNotIn("\"", out_line)
        self.assertIn(out_line, assignments_dict)

        error_lines = ["\"", "\"\"\"\"", "\"No comma\" b"]
        for line in error_lines:
            self.assertRaises(SirilError, string_parsing, line, assignments_dict)

        assignments_dict = self.new_assignments_dict
        line = "assignment, \"string\", repeat({/123/:\"@\", break})"
        out_line, assignments_dict = string_parsing(line, assignments_dict)
        self.assertIn(("\"string\"",), assignments_dict.values())
        self.assertIn(("\"@\"",), assignments_dict.values())
        self.assertNotIn(("assignment",) ,assignments_dict.values())
        self.assertNotIn(("break",), assignments_dict.values())
        self.assertRegex(out_line, r"assignment, `@[0-9]+@`, repeat\(\{/123/:`@[0-9]+@`, break\}\)")


class TestFunction(TestCase):
    def setUp(self):
        self.default_assignments_dict = default_assignments_dict.copy()
        self.default_statements = default_statements.copy()
        self.file = DummyFile()
        self.default_assignments_dict["`@output@`"] = self.file

    @property
    def new_assignments_dict(self):
        return self.default_assignments_dict.copy()

    def test_dynamic_assignment(self):
        assignments_dict = self.new_assignments_dict
        assign = dynamic_assignment("Test", ("TEST",))
        self.assertNotIn("Test", assignments_dict)
        _, _, return_assignments_dict = assign((), self.new_assignments_dict)
        self.assertNotIn("Test", assignments_dict)
        self.assertIn("Test", return_assignments_dict)
        self.assertSequenceEqual(("TEST",), return_assignments_dict["Test"])

        def call(comp):
            return comp.upper()

        assign_callable = dynamic_assignment("recall", call)
        _, _, return_assignments_dict = assign_callable("Should be a comp", self.new_assignments_dict)
        self.assertNotIn("recall", assignments_dict)
        self.assertIn("recall", return_assignments_dict)
        self.assertEqual("Should be a comp".upper(), return_assignments_dict["recall"])
        _, _, return_assignments_dict = assign_callable("Take 2", self.new_assignments_dict)
        self.assertEqual("Take 2".upper(), return_assignments_dict["recall"])
