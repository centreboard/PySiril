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

    def dump(self, open_file):
        if self.buffer:
            print(self.read(), file=open_file)
