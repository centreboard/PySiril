import logging


logging.basicConfig(filename='PySiril.log', level=logging.DEBUG, filemode="w")
logger = logging.getLogger(__name__)


class SirilError(Exception):
    def __init__(self, msg, *args):
        logger.error(msg)
        super().__init__(msg, *args)
    pass


class StopRepeat(Exception):
    pass


class StopProof(Exception):
    def __init__(self, comp, *args):
        self.comp = comp
        logger.info("StopProof")
        super().__init__(*args)


class MethodImportError(Exception):
    def __init__(self, title, *args):
        logger.error("MethodImportError: {}".format(title))
        super().__init__(title, *args)
