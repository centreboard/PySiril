class SirilError(Exception):
    pass


class StopRepeat(Exception):
    pass


class StopProof(Exception):
    def __init__(self, comp, *args):
        self.comp = comp
        super().__init__(args)


class MethodImportError(Exception):
    pass
