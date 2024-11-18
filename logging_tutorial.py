import logging
'''
logging.basicConfig(
    level=logging.DEBUG,
    format="{asctime}:{filename}:{levelname}:{name}:\n\t{message}",
    style="{",
    filename="log/app.log",
    encoding='utf-8',
    filemode='a'
)
logging.debug("This is a debug message")

logging.info("This is an info message")

logging.warning("This is a warning message")

logging.error("This is an error message")

logging.critical("This is a critical message")'''

logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("log/app.log", 
                                   mode="a", encoding="utf-8")

logger.setLevel(logging.DEBUG)
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.WARNING)

logger.addHandler(console_handler)
logger.addHandler(file_handler)
formatter = logging.Formatter(
    "{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)
console_handler.setFormatter(formatter)

logger.debug('uninportant')
logger.info('hey')
logger.warning("Watch out!")


def show_only_debug(record: logging.LogRecord):
    return record.levelname == "DEBUG"
console_handler.addFilter(show_only_debug)
