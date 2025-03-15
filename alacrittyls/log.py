import logging

FORMAT = "[ %(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"

logging.basicConfig(filename="pygls.log", filemode="w", level=logging.DEBUG, format=FORMAT)

log = logging.getLogger(__name__)

