import tkinter as tk
from SirilParser import default_assignments_dict, default_statements
from PySiril import try_prove, try_parse


# Setup tkinter
class Main:
    def __init__(self, assignments_dict=None, statements=None, case_sensitive=True):
        self.assignments_dict = default_assignments_dict.copy() if assignments_dict is None else assignments_dict
        self.statements = default_statements.copy() if statements is None else statements
        self.case_sensitive = case_sensitive
        self.file = DummyFile()
        self.assignments_dict["`@output@`"] = self.file

        self.root = tk.Tk()
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill="both", expand="yes")
        self.root.wm_title("PySiril")
        self.text_in = tk.Text(self.root)
        self.text_in.pack(side="left")
        self.text_out = tk.Text(self.root)
        self.text_out.pack(side="right")
        self.text_out.config(state="disabled")
        self.prove_button = tk.Button(self.root, text="Prove", command=self.run_proof)
        self.prove_button.pack(side="top")

        self.root.mainloop()

    def run_proof(self):
        # Flush the buffer
        self.file.read()
        siril = self.text_in.get(1.0, tk.END)
        print(siril)
        truth = None
        assignments_dict, statements, index, success = try_parse(siril, self.case_sensitive,
                                                                 self.assignments_dict.copy(), self.statements.copy(),
                                                                 1, 0, True)
        if success:
            statements, truth = try_prove(assignments_dict, statements, 0)
        print(str(self.file))
        self.text_out.config(state="normal")
        self.text_out.delete(1.0, tk.END)
        self.text_out.insert(1.0, self.file.read())
        if truth == 3:
            self.text_out.config(foreground="green")
        elif truth:
            self.text_out.config(foreground="blue")
        else:
            self.text_out.config(foreground="red")
        self.text_out.config(state="disabled")


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


if __name__ == '__main__':
    Main()