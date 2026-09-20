import logging


LOGGER_NAME = "assises"


def get_logger(name=LOGGER_NAME):
    return logging.getLogger(name if name else LOGGER_NAME)


def configure_logging(level=logging.INFO):
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(levelname)s %(name)s: %(message)s",
        )