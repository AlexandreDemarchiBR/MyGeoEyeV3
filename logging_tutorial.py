import logging
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

logging.critical("This is a critical message")