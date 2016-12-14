import logging


logging.basicConfig(filename='PySiril.log', level=logging.INFO, filemode="w")
logger = logging.getLogger(__name__)


class SirilError(Exception):
    def __init__(self, msg, *args):
        logger.error("SirilError: {}".format(msg))
        super().__init__(msg, *args)
    pass


class StopRepeat(Exception):
    pass


class StopProof(Exception):
    def __init__(self, comp, *args):
        self.comp = comp
        logger.info("StopProof")
        super().__init__(*args)


class MethodImportError(SirilError):
    def __init__(self, title, *args):
        super().__init__("MethodImportError: {}".format(title), *args)


class ImportFileNotFound(SirilError, FileNotFoundError):
    def __init__(self, file_name, *args):
        super().__init__("ImportFileNotFound: {}".format(file_name), args)
